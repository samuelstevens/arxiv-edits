import random, os, csv, string
from typing import Dict, Tuple, List, Optional
from collections import Counter

from tqdm import tqdm

from arxivedits import diff, util
from arxivedits.alignment.align import Alignment
from arxivedits.alignment.sentence import SentenceID
from arxivedits.alignment.util import preprocess_single_sent

random.seed(0)


SentencePair = Tuple[Optional[SentenceID], Optional[SentenceID]]

# sentence pair to list of labels, explanation, sentence 1, sentence 2
AnnotatedPairDict = Dict[SentencePair, Tuple[List[str], str, str, str]]

# sentence id 1, sentence id 2, sentence 1, sentence 2
Edit = Tuple[Optional[SentenceID], Optional[SentenceID], str, str]

AnnotatedEdit = Tuple[
    List[str], str, Optional[SentenceID], Optional[SentenceID], str, str
]

AlignmentLookup = Dict[Tuple[str, int, int], Alignment]

# documents used for labeling edit types
EDIT_TYPE_SAMPLE = [
    ("1512.05089", 1, 2),  # done (entire)
    ("math-0104116", 1, 2),  # done (entire)
    ("0803.2581", 1, 2),  # done (entire)
    ("1306.1389", 1, 2),  # done (entire)
    ("1906.06209", 1, 2),  # done (entire)
    ("1004.1666", 1, 2),  # done (entire)
    ("1902.05725", 1, 2),  # done (entire)
    ("1409.3945", 2, 3),  # did intro
    ("1410.4028", 1, 2),  # did conclusion
    ("1610.01333", 1, 2),  # did conclusion
    ("1305.6088", 1, 2),  # no conclusion because I chopped it off (detex error?)
    ("1406.2192", 1, 2),  # did conclusion
    ("1102.5645", 1, 2),  # did conclusion
    ("cond-mat-0602186", 4, 5),  # did conclusion
    ("1412.6539", 2, 3),  # all math
    ("1204.5014", 1, 2),  # no conclusion
    ("1806.05893", 1, 2),  # source files are missing a conclusion in v2
    ("1811.07450", 1, 2),  # no conclusion
]

assert len(set(EDIT_TYPE_SAMPLE)) == len(EDIT_TYPE_SAMPLE)


def load_gold_alignments(
    sample: Optional[List[Tuple[str, int, int]]] = None
) -> AlignmentLookup:
    """
    Loads the gold alignments for a sample (best_sample is default)
    """
    if not sample:
        sample = EDIT_TYPE_SAMPLE

    return {
        (arxivid, v1, v2): Alignment.load_csv(arxivid, v1, v2)
        for arxivid, v1, v2 in tqdm(sample)
    }


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
    """
    Given a list of edits, label all the copy edits and return them
    """
    result = {}
    for sent_id1, sent_id2, sent1, sent2 in all_edits:
        is_copy, label, reason = is_copy_edit(sent1, sent2)
        if is_copy:
            result[(sent_id1, sent_id2)] = ([label], reason)

    return result


def get_all_edits(
    arxivid: str, v1: int, v2: int, gold_alignments: AlignmentLookup
) -> List[Edit]:
    """
    Returns a list all the original edits for a document pair
    """

    pairs: List[Edit] = []

    model = gold_alignments[(arxivid, v1, v2)]
    v1_ids = sorted(set(model.alignments1.keys()))
    remaining_v2_ids = set(model.alignments2.keys())

    for sent_id1 in v1_ids:
        if not model.is_aligned(sent_id1) and not diff.is_boring(
            model.lookup[sent_id1]
        ):
            # this is a deleted sentence
            pairs.append((sent_id1, None, model.lookup[sent_id1], ""))

    for sent_id1 in v1_ids:
        if not model.is_aligned(sent_id1):
            continue

        if (
            len(model.alignments1[sent_id1]) == 1
            and model.lookup[util.get(model.alignments1[sent_id1])]
            == model.lookup[sent_id1]
        ):
            for sent_id2 in model.alignments1[sent_id1]:
                if sent_id2 in remaining_v2_ids:
                    remaining_v2_ids.remove(sent_id2)
            continue  # identical

        if diff.is_boring(model.lookup[sent_id1]):
            # remove sentences aligned to boring sentences
            for sent_id2 in model.alignments1[sent_id1]:
                if sent_id2 in remaining_v2_ids:
                    remaining_v2_ids.remove(sent_id2)
            continue

        for sent_id2 in sorted(model.alignments1[sent_id1]):
            # add all non-identical, non-boring pairs
            pairs.append(
                (sent_id1, sent_id2, model.lookup[sent_id1], model.lookup[sent_id2],)
            )
            if sent_id2 in remaining_v2_ids:
                remaining_v2_ids.remove(sent_id2)

    for sent_id2 in sorted(remaining_v2_ids):  # should only be inserted ids
        sentence = model.lookup[sent_id2]
        not_aligned = not model.is_aligned(sent_id2)
        is_boring = diff.is_boring(sentence)

        assert not_aligned or is_boring

        if not is_boring:
            pairs.append((None, sent_id2, "", sentence))  # append inserts

    return pairs


def read_annotated_pairs(filename: str) -> AnnotatedPairDict:
    """
    Reads a .csv file to get all the stored annotations from it
    """

    if not os.path.isfile(filename):
        return {}

    annotated_labels: AnnotatedPairDict = {}

    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)

        for *labels, message, sent_id1_str, sent_id2_str, sent1, sent2 in reader:
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


def merge_annotations(
    arxivid: str, v1: int, v2: int, gold_alignments: AlignmentLookup
) -> int:
    """
    Loads all annotations from manual annotation, existing annotation and from automatic annotation (right now just copy edits) and writes them to the existing annotation's file. Returns the number of unlabeled edits.
    """

    newly_annotated_edits = read_annotated_pairs(
        get_annotated_filename(arxivid, v1, v2)
    )
    other_annotated_edits = read_annotated_pairs(get_raw_filename(arxivid, v1, v2))

    all_edits = get_all_edits(arxivid, v1, v2, gold_alignments)
    copy_editing_edits = get_copy_editing_edits(all_edits)

    edit_list = []
    unlabeled = 0

    for sent_id1, sent_id2, sent1, sent2 in all_edits:

        if (sent_id1, sent_id2) in copy_editing_edits:
            labels, msg = copy_editing_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        elif (sent_id1, sent_id2) in newly_annotated_edits:
            labels, msg, _, _ = newly_annotated_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        elif (sent_id1, sent_id2) in other_annotated_edits:
            labels, msg, _, _ = other_annotated_edits[(sent_id1, sent_id2)]
            edit_list.append((labels, msg, sent_id1, sent_id2, sent1, sent2))

        else:
            if sent_id1 and sent_id2:
                unlabeled += 1

            edit_list.append(([], "", sent_id1, sent_id2, sent1, sent2))

    annotated_pairs_to_csv(edit_list, arxivid, v1, v2)

    # code to produce a sample of insert/delete edits. Since I decided that these edits were boring to label (all elaboration or simplification), I've commented this code out.

    # inserted_deleted = [
    #     (labels, msg, sent_id1, sent_id2, sent1, sent2)
    #     for labels, msg, sent_id1, sent_id2, sent1, sent2 in edit_list
    #     if not sent_id1 or not sent_id2
    # ]

    # random.shuffle(inserted_deleted)

    # inserted_deleted_sample = inserted_deleted[:12]

    # unlabeled_sample = [
    #     (id1, id2)
    #     for labels, msg, id1, id2, _, _, in inserted_deleted_sample
    #     if not labels or not msg
    # ]

    # if unlabeled_sample:
    #     print(len(unlabeled_sample))
    #     pprint(unlabeled_sample)

    return unlabeled


def is_bad_label(label: str) -> bool:
    """
    Checks if a label is "bad", which means domain knowledge or pdf required.
    """
    return label == "domain knowledge" or label == "pdf required"


def visualize(sample: Optional[List[Tuple[str, int, int]]] = None) -> None:
    if not sample:
        sample = EDIT_TYPE_SAMPLE

    annotation_list = [read_annotated_pairs(get_raw_filename(*doc)) for doc in sample]
    annotations = util.merge_dicts(*annotation_list)

    annotations = {
        (sent_id1, sent_id2): annotations[(sent_id1, sent_id2)]
        for sent_id1, sent_id2 in annotations
        if sent_id1 and sent_id2
    }  # remove any inserted or deleted sentences since they're not interesting

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


def main() -> None:
    gold_alignments = load_gold_alignments()
    for arxivid, v1, v2 in EDIT_TYPE_SAMPLE:
        unlabeled = merge_annotations(arxivid, v1, v2, gold_alignments)
        print(f"{arxivid}: {unlabeled}")


if __name__ == "__main__":
    main()
