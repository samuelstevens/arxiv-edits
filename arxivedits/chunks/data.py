import csv
import os
from typing import List, Set, Dict

from tqdm import tqdm

from arxivedits import data, diff, util
from arxivedits.alignment.align import Alignment
from arxivedits.alignment.sentence import SentenceID
from arxivedits.alignment.util import save_preprocess_sent_dict
from arxivedits.chunks.lookup import SimilarityLookup, load_lookup
from arxivedits.chunks.features import FeatureVector
from arxivedits.chunks import features

ADDED = "added"
REMOVED = "removed"
BOTH = "both"
IN_CHUNK = 1
NOT_IN_CHUNK = 0


def group_asserts(group: str, both: bool = False) -> None:
    if not both:
        assert group in (
            ADDED,
            REMOVED,
        ), f"group must be one of '{ADDED}' or '{REMOVED}', not '{group}'"
    else:
        assert group in (
            ADDED,
            REMOVED,
            BOTH,
        ), f"group must be one of '{ADDED}', '{REMOVED}' or '{BOTH}', not '{group}'"


def get_relevant_alignment(
    alignment: Alignment, group: str
) -> Dict[SentenceID, Set[SentenceID]]:
    """
    Gets either alignments1 or alignments2, depending on the `group` passed in.
    """
    group_asserts(group)
    if group == ADDED:
        relevant_alignment = alignment.alignments2
    if group == REMOVED:
        relevant_alignment = alignment.alignments1

    return relevant_alignment


def get_chunks(
    alignment: Alignment, min_length: int, group: str
) -> List[List[SentenceID]]:
    """
    Gets all consecutive blocks for a `Group`

    Parameters
    ----------
    alignment : Alignment
        Gold alignment for a document.

    min_length : int
        the minimum length for a removed chunk

    group : str
        either 'added' or 'removed'
    """

    group_asserts(group)

    doc = sorted(get_relevant_alignment(alignment, group).keys())

    chunks = util.consecutive_values(
        doc,
        lambda sent_id: (
            not alignment.is_aligned(sent_id)  # removed
            or diff.is_boring(alignment.lookup[sent_id])  # boring, so we don't care
        ),
    )

    chunks = [chunk for chunk in chunks if len(chunk) >= min_length]

    return chunks


def sents_not_solved_by_diff(
    arxivid: str, v1: int, v2: int, group: str
) -> Set[SentenceID]:
    """
    Returns a set of sentenceIDs that are not aligned, are not identical (not solved by line_diff), and are not boring.
    """

    diff_alignment = Alignment.load(arxivid, v1, v2)

    group_asserts(group)
    relevant_alignment = get_relevant_alignment(diff_alignment, group)

    result = set()

    for sent_id in relevant_alignment.keys():
        if not diff_alignment.is_aligned(sent_id) and not diff.is_boring(
            diff_alignment.lookup[sent_id]
        ):
            result.add(sent_id)

    return result


def get_examples_from(
    arxivid: str, v1: int, v2: int, min_length: int, window_size: int, group: str
) -> List[List[float]]:
    """
    1. Load the annotated alignment and similarity lookup.
    2. Find all the sentences in the relevant version of a document.
    3. Find positive examples of removed chunks (in a group of MIN_LENGTH)
    4. Find negative examples of chunks (sentences that are not aligned, but not in a big enough group, and not boring)
    6. Use a sliding window, and whether the middle sentence is in positive or negative to determine gold label.
    7. Convert these sentences to feature vectors with labels.
    8. Write these feature vectors with labels to .csv file.
    """

    group_asserts(group)

    examples = []

    # 1. Load the annotated alignment and similarity lookup.
    gold_alignment = Alignment.load(arxivid, v1, v2)
    similarity_lookup = load_lookup(arxivid, v1, v2)
    relevant_gold_alignment = get_relevant_alignment(gold_alignment, group)

    # 2. Find all the sentences in the relevant version of a document.
    sent_ids = [
        i
        for i in sorted(relevant_gold_alignment.keys())
        if not diff.is_boring(gold_alignment.lookup[i])
    ]

    # 3. Find positive examples of chunks (in a group of MIN_LENGTH)
    sentences_in_chunk = set(
        util.flatten(get_chunks(gold_alignment, min_length, group))
    )

    # 4. Find negative examples of chunks (sentences that are not aligned, but not in a big enough group, and not boring)
    sentences_not_in_chunk = (
        sents_not_solved_by_diff(arxivid, v1, v2, group) - sentences_in_chunk
    )

    assert (
        not sentences_in_chunk & sentences_not_in_chunk
    ), f"There should be no common values between the positive and negative examples. However, there are: {sentences_in_chunk & sentences_not_in_chunk}"

    sentence_features = []

    def get_label(sent_id: SentenceID) -> int:
        if sent_id in sentences_in_chunk:
            return IN_CHUNK
        elif sent_id in sentences_not_in_chunk:
            return NOT_IN_CHUNK
        else:
            assert gold_alignment.is_aligned(
                sent_id
            ), f"Since {sent_id} is not positive or negative, it must be aligned."
            return NOT_IN_CHUNK

    # 6. Use a sliding window, and whether the middle sentence is in positive or negative to determine gold label.
    for _id in sent_ids:
        sentence_features.append(
            # 7. Convert these sentences to feature vectors.
            (
                features.make_feature_vector(
                    gold_alignment.lookup[_id],
                    similarity_lookup.get_sentence_vector(gold_alignment.lookup[_id]),
                ),
                get_label(_id),
            )
        )

    # 8. Convert individual sentence features to a feature vector
    for feature_tuple in util.sliding_window(
        sentence_features,
        size=window_size,
        default_value=(FeatureVector.default(), NOT_IN_CHUNK),
    ):
        assert len(feature_tuple) % 2 == 1, f"{feature_tuple} should be an odd length."

        middle_index = len(feature_tuple) // 2

        prev = feature_tuple[:middle_index]
        after = feature_tuple[middle_index + 1 :]

        feat, label = feature_tuple[middle_index]

        feature_vector: List[float] = []

        for f, _ in prev:
            feature_vector.extend(f.to_list())

        feature_vector.extend(feat.to_list())

        for f, _ in after:
            feature_vector.extend(f.to_list())

        feature_vector.append(label)

        examples.append(feature_vector)

    return examples


def write_data(
    min_length: int, window_size: int, group: str, repeat: bool = True
) -> None:
    """
    Writes removed/added data to .csv files. Doesn't do anything if the files already exist.
    """

    group_asserts(group)

    filename = os.path.join(
        data.ALIGNMENT_DIR,
        "chunks",
        "data",
        f"{group}-examples-{window_size}-{min_length}.csv",
    )

    if os.path.isfile(filename) and not repeat:
        return

    examples = []

    for arxivid, v1, v2 in tqdm(data.ANNOTATED_IDS):  # [('1902.05725', 1, 2)]:
        examples.extend(
            get_examples_from(arxivid, v1, v2, min_length, window_size, group)
        )

    with open(filename, "w") as file:
        csvwriter = csv.writer(file, dialect="excel")

        for f in examples:
            csvwriter.writerow(f)


def write_data_DEPRECATED(
    min_length: int, window_size: int, repeat: bool = False
) -> None:
    """
    Writes removed/added data to .csv files. Doesns't do anything if the files already exist.
    """
    added_filename = os.path.join(
        data.ALIGNMENT_DIR,
        "chunks",
        "data",
        f"added-examples-{window_size}-{min_length}.csv",
    )

    removed_filename = os.path.join(
        data.ALIGNMENT_DIR,
        "chunks",
        "data" f"removed-examples-{window_size}-{min_length}.csv",
    )

    if (
        os.path.isfile(added_filename)
        and os.path.isfile(removed_filename)
        and not repeat
    ):
        return

    added_examples = []
    removed_examples = []

    for arxivid, v1, v2 in tqdm(data.ANNOTATED_IDS):  # [('1902.05725', 1, 2)]:
        # 1. Load the annotated alignment.
        alignment = Alignment.load(arxivid, v1, v2)

        similarity_lookup = SimilarityLookup(arxivid, v1, v2)

        # 2. Find all the non-boring sentences in v1 of a document
        # because we don't want to include them (boring sentences)
        # in our predictions or in the features for other sentences.
        v1_sent_ids = [
            i
            for i in sorted(alignment.alignments1.keys())
            if not diff.is_boring(alignment.lookup[i])
        ]

        # 3. Find positive examples of removed sentences (in a group of MIN_LENGTH)
        removed_sentences_pos = set(
            util.flatten(get_chunks(alignment, min_length, REMOVED))
        )
        # 4. Find negative examples of removed sentences (removed, but not in a big enough group, and not boring)
        not_in_diff = sents_not_solved_by_diff(arxivid, v1, v2, REMOVED)
        removed_sentences_neg = not_in_diff - removed_sentences_pos

        assert (
            len(removed_sentences_pos & removed_sentences_neg) == 0
        ), f"There should be no common values between the positive and negative examples. However, there are: {removed_sentences_pos & removed_sentences_neg}"

        removed_features = []

        # 6. Use a sliding window
        for _id in v1_sent_ids:
            if _id in removed_sentences_pos:
                label = 1
            elif _id in removed_sentences_neg:
                label = 0
            else:
                assert alignment.is_aligned(
                    _id
                ), f"Since {_id} is not positive or negative, it must be aligned."
                continue

            removed_features.append(
                # 8. Convert these sentences to feature vectors.
                (
                    features.make_feature_vector(
                        alignment.lookup[_id],
                        similarity_lookup.get_sentence_vector(alignment.lookup[_id]),
                    ),
                    label,
                )
            )

        # 2. Find all the non-boring sentences in v2 of a document
        # because we don't want to include them (boring sentences)
        # in our predictions or in the features for other sentences.
        v2_sent_ids = [
            i
            for i in sorted(alignment.alignments2.keys())
            if not diff.is_boring(alignment.lookup[i])
        ]

        # 3. Find positive examples of added sentences (in a group of MIN_LENGTH)
        added_sentences_pos = set(
            util.flatten(get_chunks(alignment, min_length, ADDED))
        )

        # 4. Find negative examples of added sentences (removed, but not in a big enough group, and not boring)
        not_in_diff = sents_not_solved_by_diff(arxivid, v1, v2, ADDED)
        added_sentences_neg = not_in_diff - added_sentences_pos

        assert (
            len(added_sentences_pos & added_sentences_neg) == 0
        ), f"There should be no common values between the positive and negative examples. However, there are: {added_sentences_pos & added_sentences_neg}"

        added_features = []

        # 6. Use a sliding window
        for _id in v2_sent_ids:
            if _id in added_sentences_pos:
                label = 1
            elif _id in added_sentences_neg:
                label = 0
            else:
                assert alignment.is_aligned(
                    _id
                ), f"Since {_id} is not positive or negative, it must be aligned."
                continue

            added_features.append(
                # 8. Convert these sentences to feature vectors.
                (
                    features.make_feature_vector(
                        alignment.lookup[_id],
                        similarity_lookup.get_sentence_vector(alignment.lookup[_id]),
                    ),
                    label,
                )
            )

        for feature_tuple in util.sliding_window(
            removed_features,
            size=window_size,
            default_value=(FeatureVector.default(), 0),
        ):
            assert (
                len(feature_tuple) % 2 == 1
            ), f"{feature_tuple} should be an odd length."

            middle_index = len(feature_tuple) // 2

            prev = feature_tuple[:middle_index]
            after = feature_tuple[middle_index + 1 :]

            feat, label = feature_tuple[middle_index]

            feature_vector: List[float] = []

            for f, _ in prev:
                feature_vector.extend(f.to_list())

            feature_vector.extend(feat.to_list())

            for f, _ in after:
                feature_vector.extend(f.to_list())

            feature_vector.append(label)

            removed_examples.append(feature_vector)

        for feature_tuple in util.sliding_window(
            added_features,
            size=window_size,
            default_value=(FeatureVector.default(), 0),
        ):
            assert (
                len(feature_tuple) % 2 == 1
            ), f"{feature_tuple} should be an odd length."

            middle_index = len(feature_tuple) // 2

            prev = feature_tuple[:middle_index]
            after = feature_tuple[middle_index + 1 :]

            feat, label = feature_tuple[middle_index]

            feature_vector = []

            for f, _ in prev:
                feature_vector.extend(f.to_list())

            feature_vector.extend(feat.to_list())

            for f, _ in after:
                feature_vector.extend(f.to_list())

            feature_vector.append(label)

            added_examples.append(feature_vector)

    # 8. Write these feature vectors to a csv file with a target label.
    with open(added_filename, "w") as file:
        csvwriter = csv.writer(file, dialect="excel")

        for f in added_examples:
            csvwriter.writerow(f)

    # 8. Write these feature vectors to a csv file with a target label.
    with open(removed_filename, "w") as file:
        csvwriter = csv.writer(file, dialect="excel")

        for f in removed_examples:
            csvwriter.writerow(f)


def main() -> None:
    for length in range(5, 13):
        for window in range(1, 4):
            write_data(length, window, ADDED, True)
            write_data(length, window, REMOVED, True)

    save_preprocess_sent_dict()


if __name__ == "__main__":
    main()
