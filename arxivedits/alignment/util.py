import functools

from typing import List


from arxivedits import util, diff, preprocess
from arxivedits.alignment.structures import SentenceStruct, STATUS


def is_sentence_solved(sentence: SentenceStruct) -> bool:
    return sentence.status != STATUS.UNKNOWN


def is_paragraph_solved(paragraph: List[SentenceStruct]) -> bool:
    """
    Returns whether all removed sentences (OLD SENTENCES) in a paragraph have been aligned.
    """
    return all(
        [
            is_sentence_solved(sentence)
            for sentence in paragraph
            if sentence.diff.code == -1
        ]
    )


@functools.lru_cache(maxsize=512)
def similar(sent1: str, sent2: str) -> bool:
    sent1 = preprocess.preprocess_sent(sent1)

    sent2 = preprocess.preprocess_sent(sent2)

    diff_output = diff.line_diff(util.sent_to_words(sent1), util.sent_to_words(sent2))

    length_removed = sum([len(words) for code, words in diff_output if code == -1])
    length_original = sum(
        [len(words) for code, words in diff_output if code in [-1, 0]]
    )
    length_added = sum([len(words) for code, words in diff_output if code == 1])
    length_new = sum([len(words) for code, words in diff_output if code in [1, 0]])

    return (
        (
            length_original != 0
            and length_new != 0
            and length_removed / length_original <= 0.2
            and length_added / length_original <= 0.4
            # consider changing to length_new
        )
        or sent1 in sent2  # TODO: is this too loose a filter?
        or sent2 in sent1  # TODO: is this too loose a filter?
    )
