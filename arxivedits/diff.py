from typing import List, Tuple
import functools
import re
import string

from diff_match_patch import diff_match_patch

from arxivedits.detex.constants import (
    INLINE_MATH_TAG,
    BLOCK_MATH_TAG,
    CITE_TAG,
    REF_TAG,
)

RawDiff = List[Tuple[int, str]]
ParagraphDiff = List[Tuple[int, List[str]]]
LineDiff = List[Tuple[int, str]]


# can't cache this because the lines are unhashable
def line_diff(lines1: List[str], lines2: List[str]) -> LineDiff:
    """
    Calculates a line by line difference of two texts.
    """

    if isinstance(lines1, str) or isinstance(lines2, str):
        raise TypeError(
            "I changed the method signature on line_diff to accept lists of strings now. It will join them on '\\n' itself now. Sorry!"
        )

    text1 = "\n".join(lines1)
    text2 = "\n".join(lines2)

    diff = _hashable_line_diff(text1, text2)

    sent_diff = []
    for code, text in diff:
        cleaned_text = text[:-1] if text[-1] == "\n" else text
        sent_diff.extend([(code, s) for s in cleaned_text.split("\n")])

    return sent_diff


@functools.lru_cache(maxsize=4096)  # YOU MUST CLEAR THIS CACHE
def _hashable_line_diff(text1: str, text2: str) -> RawDiff:
    dmp = diff_match_patch()
    line_text1, line_text2, line_arr = dmp.diff_linesToChars(text1, text2)
    diff: RawDiff = dmp.diff_main(line_text1, line_text2, False)
    dmp.diff_charsToLines(diff, line_arr)
    return diff


def paragraph_diff(doc1: List[List[str]], doc2: List[List[str]]) -> ParagraphDiff:
    """
    Calculates a paragraph difference of two documents, which is a list of lists of sentences.
    """

    sent_split_token = "<SENT>"

    p1 = [sent_split_token.join(sentences) for sentences in doc1]

    p2 = [sent_split_token.join(sentences) for sentences in doc2]

    diffs = line_diff(p1, p2)

    paragraphs = []
    for code, text in diffs:
        paragraphs.extend([(code, e) for e in text.split("\n") if e])

    return [(d[0], d[1].split(sent_split_token)) for d in paragraphs]


def get_keeps(diffs: RawDiff) -> int:
    keeps = [text for code, text in diffs if code == 0]

    sentences_kept = sum([text.count("\n") for text in keeps]) + 1

    return sentences_kept


def get_additions(diffs: RawDiff) -> int:
    additions = [text for code, text in diffs if code > 0]

    sentences_added = sum([text.count("\n") for text in additions])

    return sentences_added


def get_deletions(diffs: RawDiff) -> int:
    deletions = [text.rstrip() for code, text in diffs if code < 0]

    sentences_deleted = sum([text.count("\n") for text in deletions])

    return sentences_deleted


def get_unaligned_line_distribution(diffs: ParagraphDiff) -> List[int]:
    lengths_of_consecutive_different_paragraphs = []
    pgidx = 0
    modified = 0
    while pgidx < len(diffs) and diffs[pgidx][0] != 0:
        if diffs[pgidx][0] == -1:
            modified += 1
        pgidx += 1

    if pgidx > 0:
        lengths_of_consecutive_different_paragraphs.append(modified)

    FLAG_in_identical = True
    length = 0
    while pgidx < len(diffs):
        code = diffs[pgidx][0]

        if code == 0 and FLAG_in_identical:
            pass
        elif code == -1 and FLAG_in_identical:
            FLAG_in_identical = False
            length += 1
        elif code == 0 and not FLAG_in_identical:
            FLAG_in_identical = True
            lengths_of_consecutive_different_paragraphs.append(length)
            length = 0
        elif code == -1 and not FLAG_in_identical:
            length += 1

        pgidx += 1

    if not FLAG_in_identical:
        lengths_of_consecutive_different_paragraphs.append(length)

    return lengths_of_consecutive_different_paragraphs


@functools.lru_cache(maxsize=512)
def sent_filter(sent: str) -> bool:
    """
    Returns `True` is a sentence is a good sentence, `False` if a sentence shouldn't be considered.
    """
    j = sent

    if re.match("^#+ .", j) is not None:
        return True

    len_no_punctuation = len([i for i in sent.split() if i not in string.punctuation])
    len_no_punctuation_no_special_tokens_no_number = len(
        [
            i
            for i in sent.split()
            if i not in string.punctuation
            and i not in [INLINE_MATH_TAG, BLOCK_MATH_TAG, CITE_TAG, REF_TAG]
            and not i.isnumeric()
        ]
    )

    count_special_tokens = (
        j.count(INLINE_MATH_TAG)
        + j.count(BLOCK_MATH_TAG)
        + j.count(REF_TAG)
        + j.count(CITE_TAG)
    )

    #     print(len_no_punctuation_no_special_tokens)
    if len_no_punctuation_no_special_tokens_no_number <= 3:
        return False

    if count_special_tokens >= 0.5 * len_no_punctuation:
        return False

    j = j.replace(INLINE_MATH_TAG, " ")
    j = j.replace(BLOCK_MATH_TAG, " ")
    j = j.replace(REF_TAG, " ")
    j = j.replace(CITE_TAG, " ")

    if [jj for jj in j if jj != " "]:
        score = (
            len([jj for jj in j if re.match("[a-zA-Z]", jj) is not None])
            + count_special_tokens
        ) / (len([jj for jj in j if jj != " "]) + count_special_tokens)
        if score <= 0.7:
            return False
    else:
        return False

    return True


def doc_filter(doc: List[List[str]]) -> List[List[str]]:
    """
    Removes all sentences that don't pass sent_filter().
    """
    clean_doc = []

    for paragraph in doc:
        clean_paragraph = [sentence for sentence in paragraph if sent_filter(sentence)]
        if clean_paragraph:
            clean_doc.append(clean_paragraph)

    return clean_doc

