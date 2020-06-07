import functools
import string
import pickle
import re
import os

from typing import List


from arxivedits import data, util, diff, tokenizer
from arxivedits.alignment.structures import SentenceStruct, STATUS

# Global initialization

tok = tokenizer.CoreNLPTokenizer()

preprocess_filename = os.path.join(data.ALIGNMENT_DIR, "preprocess_sent_dict.pkl")

with open(preprocess_filename, "rb",) as file:
    preprocess_sent_dict = pickle.load(file)


def save_preprocess_sent_dict() -> None:
    with open(preprocess_filename, "wb") as file:
        pickle.dump(preprocess_sent_dict, file)


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
def preprocess_single_sent(sent: str) -> str:
    if not sent:
        return ""

    if sent.isspace():
        return ""

    if sent in preprocess_sent_dict:
        return sent

    processed = " ".join(tok.tokenize(sent).words())

    processed = (
        processed.replace("[ MATH ]", " [MATH] ")
        .replace("[ EQUATION ]", " [EQUATION] ")
        .replace("[ REF ]", " [REF] ")
        .replace("[ CITATION ]", " [CITATION] ")
    )

    processed = " ".join(processed.split())

    preprocess_sent_dict[sent] = processed

    return processed


@functools.lru_cache(maxsize=512)
def similar(sent1: str, sent2: str) -> bool:
    if sent1 in preprocess_sent_dict:
        sent1 = preprocess_sent_dict[sent1]
    else:
        sent1 = preprocess_single_sent(sent1)

    if sent2 in preprocess_sent_dict:
        sent2 = preprocess_sent_dict[sent2]
    else:
        sent2 = preprocess_single_sent(sent2)

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
        or sent1 in sent2
        or sent2 in sent1
        # TODO: is this too loose a filter?
    )
