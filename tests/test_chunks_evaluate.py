from arxivedits.chunks.evaluate import get_metrics
from arxivedits.data import ANNOTATED_IDS
from arxivedits.alignment import Alignment
from arxivedits.diff import is_boring


def test_empty_predictions():
    predictions = set()

    for arxivid, v1, v2 in ANNOTATED_IDS:
        gold_alignment = Alignment.load(arxivid, v1, v2)

        result = get_metrics(predictions, gold_alignment)

        assert result.comps_after_removal == result.total_comps
        assert result.lost_alignments == 0


def test_predict_all_v1():
    for arxivid, v1, v2 in ANNOTATED_IDS:
        gold_alignment = Alignment.load(arxivid, v1, v2)

        predictions = set(gold_alignment.alignments1.keys())

        result = get_metrics(predictions, gold_alignment)

        assert result.comps_after_removal == 0
        assert result.lost_alignments == result.total_alignments


def test_predict_all_v2():
    for arxivid, v1, v2 in ANNOTATED_IDS:
        gold_alignment = Alignment.load(arxivid, v1, v2)

        predictions = set(gold_alignment.alignments2.keys())

        result = get_metrics(predictions, gold_alignment)

        assert result.comps_after_removal == 0
        assert result.lost_alignments == result.total_alignments


def test_predict_all():
    for arxivid, v1, v2 in ANNOTATED_IDS:
        gold_alignment = Alignment.load(arxivid, v1, v2)

        predictions = set(gold_alignment.alignments1.keys()) | set(
            gold_alignment.alignments2.keys()
        )

        result = get_metrics(predictions, gold_alignment)

        assert result.comps_after_removal == 0
        assert result.lost_alignments == result.total_alignments


# def test_predictions_from_v1():
#     for arxivid, v1, v2 in ANNOTATED_IDS:

#         gold_alignment = Alignment.load(arxivid, v1, v2)
#         new_alignment = Alignment(arxivid, v1, v2)
#         interesting_v2_sentences = [
#             _id
#             for _id in new_alignment.alignments2
#             if not new_alignment.is_aligned(_id)
#             and not is_boring(new_alignment.lookup[_id])
#         ]

#         interesting_v1_sentences = [
#             _id
#             for _id in new_alignment.alignments1
#             if not new_alignment.is_aligned(_id)
#             and not is_boring(new_alignment.lookup[_id])
#         ]

#         for i in range(min(10, len(interesting_v1_sentences))):
#             predictions = set(interesting_v1_sentences[:i])

#             result = get_metrics(predictions, gold_alignment)

#             assert result.total_comps == len(interesting_v1_sentences) * len(
#                 interesting_v2_sentences
#             )

#             assert (
#                 result.comps_after_removal + i * len(interesting_v2_sentences)
#                 == result.total_comps
#             )
