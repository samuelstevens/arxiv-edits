import random, os, csv, string
from typing import Dict, Tuple, List, Optional
from collections import Counter

from tqdm import tqdm

from pprint import pprint

from arxivedits import diff, util
from arxivedits.alignment.align import Alignment
from arxivedits.alignment.sentence import SentenceID
from arxivedits.alignment.util import preprocess_single_sent

random.seed(0)


SentencePair = Tuple[Optional[SentenceID], Optional[SentenceID]]

AnnotatedPairDict = Dict[SentencePair, Tuple[List[str], str, str, str]]
Edit = Tuple[Optional[SentenceID], Optional[SentenceID], str, str]
EditList = List[Edit]
AnnotatedEdit = Tuple[
    List[str], str, Optional[SentenceID], Optional[SentenceID], str, str
]

best_sample = [
    ("1512.05089", 1, 2),
    ("math-0104116", 1, 2),
    ("0803.2581", 1, 2),
    ("1306.1389", 1, 2),
]


def load_gold_alignments(
    sample: Optional[List[Tuple[str, int, int]]] = None
) -> Dict[Tuple[str, int, int], Alignment]:
    """
    Loads the gold alignments for a sample (best_sample is default)
    """
    if not sample:
        sample = best_sample

    return {
        (arxivid, v1, v2): Alignment.load_csv(arxivid, v1, v2)
        for arxivid, v1, v2 in tqdm(sample)
    }


GOLD_ALIGNMENTS = load_gold_alignments()

for g in GOLD_ALIGNMENTS:
    GOLD_ALIGNMENTS[g].save()


def get_annotated_filename(arxivid: str, v1: int, v2: int) -> str:
    """
    Gets the annotated edit-type filename
    """
    return f"/Users/samstevens/Dropbox/arXiv_edit_Sam_Chao/Sam_working_folder/jupyter/data/types/sample/{arxivid}-v{v1}-v{v2}-pairs-annotated.csv"


def get_raw_filename(arxivid: str, v1: int, v2: int) -> str:
    """
    Gets the raw edit-type filename (can include annotations)
    """
    return f"/Users/samstevens/Dropbox/arXiv_edit_Sam_Chao/Sam_working_folder/jupyter/data/types/sample/{arxivid}-v{v1}-v{v2}-pairs.csv"


def is_copy_edit(sent1: str, sent2: str) -> Tuple[bool, str, str]:
    """
    Checks if an edit is a simple copy edit. Returns a label and a message.
    """

    deleted_chars = [
        ch for code, ch in diff.fast_diff(list(sent1), list(sent2)) if code == -1
    ]
    added_chars = [
        ch for code, ch in diff.fast_diff(list(sent1), list(sent2)) if code == 1
    ]

    max_one_letter_or_punc_added = len(added_chars) < 2 and all(
        [
            c in string.ascii_letters + string.punctuation + string.whitespace
            for c in added_chars
        ]
    )

    max_one_letter_or_punc_deleted = len(deleted_chars) < 2 and all(
        [
            c in string.ascii_letters + string.punctuation + string.whitespace
            for c in deleted_chars
        ]
    )

    if (
        max_one_letter_or_punc_added and max_one_letter_or_punc_deleted
    ):  # allows for one letter changes
        return (
            True,
            "correction",
            "automatically classified because only up to one letter/punctuation mark was deleted and up to one letter/punctuation mark was added",
        )

    only_punctuation_deleted = all(
        [c in string.punctuation + string.whitespace for c in deleted_chars]
    )
    only_punctuation_added = all(
        [c in string.punctuation + string.whitespace for c in added_chars]
    )

    if only_punctuation_added and only_punctuation_deleted:
        return (
            True,
            "correction",
            "automatically classified because only whitespace/punctuation was added/deleted",
        )

    tokens1 = preprocess_single_sent(sent1.rstrip(".")).split()
    tokens2 = preprocess_single_sent(sent2.rstrip(".")).split()

    deleted_tokens = [
        tok for code, tok in diff.fast_diff(tokens1, tokens2) if code == -1
    ]
    added_tokens = [tok for code, tok in diff.fast_diff(tokens1, tokens2) if code == 1]

    if not added_tokens and not deleted_tokens:
        return (
            True,
            "correction",
            "automatically classified because there are only whitespace changes",
        )

    if (
        len(added_tokens) == 1
        and len(deleted_tokens) == 1
        and added_tokens == deleted_tokens
    ):
        return (
            True,
            "word usage",
            "automatically classified because exactly one token was moved within the sentence",
        )

    only_the_added = (
        len(added_tokens) == 1 and added_tokens[0] == "the"
    ) or not added_tokens
    only_the_deleted = (
        len(deleted_tokens) == 1 and deleted_tokens[0] == "the"
    ) or not deleted_tokens

    if only_the_added and only_the_deleted:  # only "the" deleted or added
        return (
            True,
            "word usage",
            "automatically classified because only the word 'the' was deleted and/or added",
        )

    return (False, "", "")


def annotated_pairs_to_csv(
    pairs: List[AnnotatedEdit], arxivid: str, v1: int, v2: int
) -> None:
    """
    Writes a list of annotated sentences to a file.
    """
    filename = get_raw_filename(arxivid, v1, v2)

    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        for _, edit in enumerate(pairs):
            labels, msg, sent_id1, sent_id2, sent1, sent2 = edit
            writer.writerow([*labels, msg, sent_id1, sent_id2, sent1, sent2])


def get_copy_editing_edits(
    all_edits: List[Edit],
) -> Dict[SentencePair, Tuple[List[str], str]]:
    result = {}
    for sent_id1, sent_id2, sent1, sent2 in all_edits:
        is_copy, label, reason = is_copy_edit(sent1, sent2)
        if is_copy:
            result[(sent_id1, sent_id2)] = ([label], reason)

    return result


def get_all_edits(arxivid: str, v1: int, v2: int) -> EditList:
    pairs: EditList = []

    alignment = GOLD_ALIGNMENTS[(arxivid, v1, v2)]
    v1_ids = set(alignment.alignments1.keys())
    v2_ids = set(alignment.alignments2.keys())
    for sent_id1 in sorted(v1_ids):
        if not alignment.is_aligned(sent_id1) and not diff.is_boring(
            alignment.lookup[sent_id1]
        ):
            pairs.append((sent_id1, None, alignment.lookup[sent_id1], ""))

    for sent_id1 in sorted(v1_ids):
        if not alignment.is_aligned(sent_id1):
            continue

        if (
            len(alignment.alignments1[sent_id1]) == 1
            and alignment.lookup[util.get(alignment.alignments1[sent_id1])]
            == alignment.lookup[sent_id1]
        ):
            for sent_id2 in alignment.alignments1[sent_id1]:
                if sent_id2 in v2_ids:
                    v2_ids.remove(sent_id2)
            continue  # identical

        if diff.is_boring(alignment.lookup[sent_id1]):
            for sent_id2 in alignment.alignments1[sent_id1]:
                if sent_id2 in v2_ids:
                    v2_ids.remove(sent_id2)
            continue

        for sent_id2 in sorted(alignment.alignments1[sent_id1]):
            pairs.append(
                (
                    sent_id1,
                    sent_id2,
                    alignment.lookup[sent_id1],
                    alignment.lookup[sent_id2],
                )
            )
            if sent_id2 in v2_ids:
                v2_ids.remove(sent_id2)

    for sent_id2 in sorted(v2_ids):  # should only be unaligned ids
        assert (not alignment.is_aligned(sent_id2)) or diff.is_boring(
            alignment.lookup[sent_id2]
        )
        if not diff.is_boring(alignment.lookup[sent_id2]):
            pairs.append((None, sent_id2, "", alignment.lookup[sent_id2]))

    return pairs


def read_annotated_pairs(filename: str) -> AnnotatedPairDict:

    annotated_labels: AnnotatedPairDict = {}

    if not os.path.isfile(filename):
        return annotated_labels

    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)

        for (
            _,
            (*labels, message, sent_id1_str, sent_id2_str, sent1, sent2),
        ) in enumerate(reader):
            labels = [l.strip() for l in labels]
            try:
                sent_id1 = SentenceID.parse(sent_id1_str) if sent_id1_str else None
                sent_id2 = SentenceID.parse(sent_id2_str) if sent_id2_str else None
            except ValueError as err:
                print(err)
                print(sent_id1)
                print(sent_id2)
                raise

            if labels and message:
                annotated_labels[(sent_id1, sent_id2)] = (labels, message, sent1, sent2)

    return annotated_labels


def merge_annotations(arxivid: str, v1: int, v2: int) -> int:
    annotated_edits = read_annotated_pairs(get_annotated_filename(arxivid, v1, v2))
    other_annotated_edits = read_annotated_pairs(get_raw_filename(arxivid, v1, v2))

    all_edits = get_all_edits(arxivid, v1, v2)
    copy_editing_edits = get_copy_editing_edits(all_edits)
    edit_list = []
    unlabeled = 0

    for sent_id1, sent_id2, sent1, sent2 in all_edits:

        if (sent_id1, sent_id2) in copy_editing_edits:
            labels, msg = copy_editing_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        elif (sent_id1, sent_id2) in annotated_edits:
            labels, msg, _, _ = annotated_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        elif (sent_id1, sent_id2) in other_annotated_edits:
            labels, msg, _, _ = other_annotated_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        else:
            unlabeled += 1

            edit_list.append(([], "", sent_id1, sent_id2, sent1, sent2))

    annotated_pairs_to_csv(edit_list, arxivid, v1, v2)

    inserted_deleted = [
        (labels, msg, sent_id1, sent_id2, sent1, sent2)
        for labels, msg, sent_id1, sent_id2, sent1, sent2 in edit_list
        if not sent_id1 or not sent_id2
    ]

    random.shuffle(inserted_deleted)

    inserted_deleted_sample = inserted_deleted[:12]

    unlabeled_sample = [
        (id1, id2)
        for labels, msg, id1, id2, _, _, in inserted_deleted_sample
        if not labels or not msg
    ]

    if unlabeled_sample:
        print(len(unlabeled_sample))
        pprint(unlabeled_sample)

    return unlabeled


required_annotations = {
    (arxivid, v1, v2): merge_annotations(arxivid, v1, v2)
    for arxivid, v1, v2 in best_sample
}


def is_bad_label(label: str) -> bool:
    return label.isupper() or label == "domain knowledge" or label == "pdf required"


def visualize() -> None:
    annotation_list = [
        read_annotated_pairs(get_raw_filename(*doc)) for doc in best_sample
    ]
    annotations = util.merge_dicts(*annotation_list)

    all_labels = []
    annotated_sents = 0

    for labels, _, _, _ in annotations.values():
        annotated_sents += 1

        if any([is_bad_label(l) for l in labels]):
            for l in labels:
                if is_bad_label(l):
                    # only append "domain knowledge" and "pdf required"
                    all_labels.append(l)

        else:
            all_labels.extend(labels)

    label_counts = Counter(all_labels)

    keys = sorted(label_counts.keys())
    values = [label_counts[k] for k in keys]

    for k, v in zip(keys, values):
        print(f"{k}: {v} \n{v / annotated_sents * 100:.1f}\\%")
    print("-----")
    print(f"total: {len(all_labels)} ({sum(label_counts.values())})")
    print(f"total labels: {annotated_sents}")


if __name__ == "__main__":
    visualize()
