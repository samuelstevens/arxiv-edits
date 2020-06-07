"""
Helper methods to evaluate whether a chunk was appropriately removed.
"""
import os
import csv
from typing import Set, Tuple, List, Union
from collections import namedtuple

from tqdm import tqdm

from arxivedits.alignment.sentence import SentenceID
from arxivedits.alignment.align import Alignment

from arxivedits.chunks import features
from arxivedits.chunks.model import train_model
from arxivedits.chunks.data import ADDED, REMOVED, BOTH, get_chunks
from arxivedits.chunks.lookup import load_lookup
from arxivedits.chunks.visualize import visualize_predictions

from arxivedits import diff, data, util, structures


Metrics = namedtuple(
    "Metrics",
    [
        "total_comps",
        "comps_after_removal",
        "total_alignments",
        "lost_alignments",
        "removed_sents",
    ],
)


def evaluate_predictions(
    predictions: Set[structures.T], target: Set[structures.T]
) -> Tuple[float, float]:
    TP = predictions & target
    FP = predictions - target
    FN = target - predictions

    precision = len(TP) / (len(TP) + len(FP)) if len(TP) + len(FP) != 0 else 0
    recall = len(TP) / (len(TP) + len(FN)) if len(TP) + len(FN) != 0 else 0

    return precision, recall


def get_metrics(
    predicted_removals: Set[SentenceID], gold_alignment: Alignment
) -> Metrics:
    """
    Returns metrics evaluating the performance of predicted sentence removals, given a gold alignment.
    """

    diff_alignment = Alignment(
        gold_alignment.arxivid, gold_alignment.version1, gold_alignment.version2
    )

    non_identical_aligned_pairs = set()

    unaligned_sents_in_v1 = set()

    for sent_id in gold_alignment.alignments1:
        if not diff.is_boring(
            gold_alignment.lookup[sent_id]
        ) and not diff_alignment.is_aligned(sent_id):
            unaligned_sents_in_v1.add(sent_id)

        if (
            not diff.is_boring(gold_alignment.lookup[sent_id])
            and gold_alignment.is_aligned(sent_id)
            and not diff_alignment.is_aligned(sent_id)
        ):
            for matched_id in gold_alignment.alignments1[sent_id]:
                if not diff.is_boring(gold_alignment.lookup[matched_id]):
                    non_identical_aligned_pairs.add((sent_id, matched_id))

    unaligned_sents_in_v2 = set()

    for sent_id in gold_alignment.alignments2:
        if not diff.is_boring(
            gold_alignment.lookup[sent_id]
        ) and not diff_alignment.is_aligned(sent_id):
            unaligned_sents_in_v2.add(sent_id)

        if (
            not diff.is_boring(gold_alignment.lookup[sent_id])
            and gold_alignment.is_aligned(sent_id)
            and not diff_alignment.is_aligned(sent_id)
        ):
            for matched_id in gold_alignment.alignments2[sent_id]:
                if not diff.is_boring(gold_alignment.lookup[matched_id]):
                    non_identical_aligned_pairs.add((matched_id, sent_id))

    total_comps = len(unaligned_sents_in_v1) * len(unaligned_sents_in_v2)

    comps_after_removal = len(unaligned_sents_in_v1 - predicted_removals) * len(
        unaligned_sents_in_v2 - predicted_removals
    )

    total_alignments = len(non_identical_aligned_pairs)

    lost_alignments = 0

    for sent_id_v1, sent_id_v2 in non_identical_aligned_pairs:
        if sent_id_v1 in predicted_removals or sent_id_v2 in predicted_removals:
            lost_alignments += 1

    removed_sents = len(predicted_removals)

    return Metrics(
        total_comps,
        comps_after_removal,
        total_alignments,
        lost_alignments,
        removed_sents,
    )


def evaluate_model(
    min_length: int, window_size: int, silent: bool = True
) -> List[float]:
    total_target = set()
    total_predictions = set()
    missed_alignments = 0
    total_alignments = 0
    total_comps_after_removal = 0
    total_sent_comps = 0
    total_removed_sents = 0

    added_model, _ = train_model(BOTH, min_length, window_size, silent=silent)
    removed_model, _ = train_model(BOTH, min_length, window_size, silent=silent)

    for arxivid, v1, v2 in tqdm(data.ANNOTATED_IDS):
        # 1. Load a document's alignment and get all the blocks of sentences that were removed.
        annotated_alignment = Alignment.load(arxivid, v1, v2)
        similarity_lookup = load_lookup(arxivid, v1, v2)

        target_removed_sentences = set(
            util.flatten(get_chunks(annotated_alignment, min_length, REMOVED))
        )
        target_added_sentences = set(
            util.flatten(get_chunks(annotated_alignment, min_length, ADDED))
        )

        # 2
        new_alignment = Alignment(arxivid, v1, v2)

        # all non-boring sentences
        v1_sent_ids = [
            _id
            for _id in sorted(new_alignment.alignments1.keys())
            if not diff.is_boring(new_alignment.lookup[_id])
        ]

        v2_sent_ids = [
            _id
            for _id in sorted(new_alignment.alignments2.keys())
            if not diff.is_boring(new_alignment.lookup[_id])
        ]

        predicted_removed_lines = []
        predicted_added_lines = []

        for ids in util.sliding_window(
            v1_sent_ids, size=window_size, default_value=None
        ):
            _id = ids[len(ids) // 2]

            if new_alignment.is_aligned(_id):
                prediction = 0
            else:
                feature_vector = []

                for sent_id in ids:
                    if not sent_id:
                        feature_vector.extend(
                            features.FeatureVector.default().to_list()
                        )
                    else:
                        feature_vector.extend(
                            features.make_feature_vector(
                                new_alignment.lookup[sent_id],
                                similarity_lookup.get_sentence_vector(
                                    new_alignment.lookup[sent_id]
                                ),
                            ).to_list()
                        )

                prediction = removed_model.predict([feature_vector]).item()

            predicted_removed_lines.append((_id, prediction))

        for ids in util.sliding_window(
            v2_sent_ids, size=window_size, default_value=None
        ):
            prediction_id = ids[len(ids) // 2]

            if new_alignment.is_aligned(prediction_id):
                prediction = 0
            else:
                feature_vector = []

                for sent_id in ids:
                    if not sent_id:
                        feature_vector.extend(
                            features.FeatureVector.default().to_list()
                        )
                    else:
                        feature_vector.extend(
                            features.make_feature_vector(
                                new_alignment.lookup[sent_id],
                                similarity_lookup.get_sentence_vector(
                                    new_alignment.lookup[sent_id]
                                ),
                            ).to_list()
                        )

                prediction = added_model.predict([feature_vector]).item()

            predicted_added_lines.append((prediction_id, prediction))

        predicted_removed_lines.extend(
            [
                (sent_id, -1)
                for sent_id in new_alignment.alignments1
                if diff.is_boring(new_alignment.lookup[sent_id])
            ]
        )

        predicted_added_lines.extend(
            [
                (sent_id, -1)
                for sent_id in new_alignment.alignments2
                if diff.is_boring(new_alignment.lookup[sent_id])
            ]
        )

        predicted_removed_lines = sorted(predicted_removed_lines)
        predicted_added_lines = sorted(predicted_added_lines)

        # 3
        predicted_removed_blocks = [
            block
            for block in util.consecutive_values(
                predicted_removed_lines, lambda pair: pair[1] == 1 or pair[1] == -1
            )
            if len(block) >= min_length
        ]

        predicted_added_blocks = [
            block
            for block in util.consecutive_values(
                predicted_added_lines, lambda pair: pair[1] == 1 or pair[1] == -1
            )
            if len(block) >= min_length
        ]

        predicted_removed_sentences = {
            sent_id for sent_id, _ in util.flatten(predicted_removed_blocks)
        }

        predicted_added_sentences = {
            sent_id for sent_id, _ in util.flatten(predicted_added_blocks)
        }

        visualize_predictions(
            sorted(annotated_alignment.alignments1.keys()),
            predicted_removed_sentences,
            target_removed_sentences,
            annotated_alignment,
            "removed",
        )

        visualize_predictions(
            sorted(annotated_alignment.alignments2.keys()),
            predicted_added_sentences,
            target_added_sentences,
            annotated_alignment,
            "added",
        )

        # "total_comps", "comps_after_removal", "total_alignments", "lost_alignments"
        metrics = get_metrics(
            predicted_removed_sentences | predicted_added_sentences, annotated_alignment
        )
        #     print(metrics, arxivid)
        missed_alignments += metrics.lost_alignments
        total_alignments += metrics.total_alignments
        total_comps_after_removal += metrics.comps_after_removal
        total_sent_comps += metrics.total_comps

        total_removed_sents += metrics.removed_sents

        total_target.update(target_removed_sentences)
        total_predictions.update(predicted_removed_sentences)

        total_target.update(target_added_sentences)
        total_predictions.update(predicted_added_sentences)

        # 6

    precision, recall = evaluate_predictions(total_predictions, total_target)
    if not silent:

        print(precision, recall, util.f_mean(precision, recall, 1))
        print("Missed alignments because of false positives:", missed_alignments)
        print(
            f"Missing alignments because of false positives: {missed_alignments / total_alignments * 100 if missed_alignments > 0 else 0:.1f}%"
        )
        print(
            "Total sentence comparisons removed:",
            total_sent_comps - total_comps_after_removal,
        )
        print(
            f"Sentence comparisons removed: {(total_sent_comps - total_comps_after_removal) / total_sent_comps * 100 if total_sent_comps > 0 else 0:.1f}%"
        )

    return [
        min_length,
        window_size,
        missed_alignments,
        missed_alignments / total_alignments * 100 if missed_alignments > 0 else 0,
        total_sent_comps - total_comps_after_removal,
        (total_sent_comps - total_comps_after_removal) / total_sent_comps * 100
        if total_sent_comps > 0
        else 0,
        total_removed_sents,
    ]


def main() -> None:
    """
    Evalutes the model.
    """
    lines: List[Union[List[float], List[str]]] = [
        [
            "min_length",
            "window_size",
            "missed_alignments",
            "missed_alignments_percent",
            "removed_comps",
            "removed_comps_percent",
            "removed_sents",
        ]
    ]
    filename = os.path.join(data.ALIGNMENT_DIR, "chunks", "results", f"chunks.csv",)

    for length in range(5, 13):
        for window in range(1, 4):
            lines.append(evaluate_model(length, window))

    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(lines)


if __name__ == "__main__":
    # print(evaluate_model(10, 3, silent=False))
    main()
