from typing import List, Tuple, Any
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
from arxivedits.lcs import lcs
from arxivedits import data, util

RawDiff = List[Tuple[int, str]]
ParagraphDiff = List[Tuple[int, List[str]]]
LineDiff = List[Tuple[int, str]]

LETTER_PATTERN = re.compile("")


def fast_diff(s1: List[str], s2: List[str]) -> List[Tuple[int, str]]:
    common = lcs(s1, s2)
    difference = []

    idx1 = 0
    idx2 = 0
    i = 0

    while i < len(common) and idx1 < len(s1) and idx2 < len(s2):
        if common[i] == s1[idx1] == s2[idx2]:
            difference.append((0, common[i]))
            i += 1
            idx1 += 1
            idx2 += 1
        elif common[i] == s1[idx1]:
            difference.append((1, s2[idx2]))
            idx2 += 1
        elif common[i] == s2[idx2]:
            difference.append((-1, s1[idx1]))
            idx1 += 1
        else:
            difference.append((-1, s1[idx1]))
            difference.append((1, s2[idx2]))
            idx1 += 1
            idx2 += 1

    assert i == len(common), f"{i}, {len(common)}"

    if idx1 < len(s1):
        difference.extend([(-1, e) for e in s1[idx1:]])

    if idx2 < len(s2):
        difference.extend([(1, e) for e in s2[idx2:]])

    return difference


# can't cache this because the lines are unhashable
def line_diff(lines1: List[Any], lines2: List[Any]) -> LineDiff:
    """
    Calculates a line by line difference of two texts.
    """

    if isinstance(lines1, str) or isinstance(lines2, str):
        raise TypeError(
            "I changed the method signature on line_diff to accept lists of strings now. It will join them on '\\n' itself now. Sorry!"
        )

    lines1 = [str(line) for line in lines1]
    lines2 = [str(line) for line in lines2]

    text1 = "\n".join(lines1)
    text2 = "\n".join(lines2)

    diff = _hashable_line_diff(text1, text2)

    sent_diff = []
    for code, text in diff:
        cleaned_text = text[:-1] if text[-1] == "\n" else text
        sent_diff.extend([(code, s) for s in cleaned_text.split("\n")])

    return sent_diff


@functools.lru_cache(maxsize=4096)  # YOU SHOULD CLEAR THIS CACHE
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

    if re.match("^#+ .", sent) is not None:
        return True

    len_no_punctuation = len(
        [tok for tok in sent.split() if tok not in string.punctuation]
    )
    len_no_punctuation_no_special_tokens_no_number = len(
        [
            tok
            for tok in sent.split()
            if tok not in string.punctuation
            and tok not in [INLINE_MATH_TAG, BLOCK_MATH_TAG, CITE_TAG, REF_TAG]
            and not tok.isnumeric()
        ]
    )

    count_special_tokens = (
        sent.count(INLINE_MATH_TAG)
        + sent.count(BLOCK_MATH_TAG)
        + sent.count(REF_TAG)
        + sent.count(CITE_TAG)
    )

    if len_no_punctuation_no_special_tokens_no_number <= 3:
        return False

    if count_special_tokens >= 0.5 * len_no_punctuation:
        return False

    sent = (
        sent.replace(INLINE_MATH_TAG, " ")
        .replace(BLOCK_MATH_TAG, " ")
        .replace(REF_TAG, " ")
        .replace(CITE_TAG, " ")
    )

    if [ch for ch in sent if ch != " "]:
        score = (len([ch for ch in sent if ch.isalpha()]) + count_special_tokens) / (
            len([ch for ch in sent if ch != " "]) + count_special_tokens
        )
        if score <= 0.7:
            return False
    else:
        return False

    return True


@functools.lru_cache(maxsize=128)
def is_title(line: str) -> bool:
    return re.match("^#+ .", line) is not None


def is_title_or_newline(line: str) -> bool:
    return line == "" or is_title(line)


@functools.lru_cache(maxsize=512)
def is_boring(sent: str) -> bool:
    """
    Checks if a sentence is boring using sent_filter(), is_title(), and is_newline()
    """
    if not sent:
        return True
    return is_title_or_newline(sent) or not sent_filter(sent)


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


def main() -> None:
    for arxivid, v1, v2 in [("1211.4814", 3, 4)]:  # util.good_id_iter():
        print(arxivid, v1, v2)
        pgs1 = data.get_paragraphs(arxivid, v1)
        pgs2 = data.get_paragraphs(arxivid, v2)

        if isinstance(pgs1, Exception):
            return

        if isinstance(pgs2, Exception):
            return

        lines1 = util.paragraphs_to_lines(pgs1)
        lines2 = util.paragraphs_to_lines(pgs2)

        for i1 in range(888, len(lines1) + 1, 1):
            for i2 in range(1178, len(lines2) + 1, 1):
                print(i1, i2)
                lines1_tmp = lines1[:i1]
                lines2_tmp = lines2[100:i2]

                # start = time.perf_counter()
                fast_diff(lines1_tmp, lines2_tmp)
                # end = time.perf_counter()

        fast_diff(lines1_tmp, lines2_tmp)

        # start = time.perf_counter()
        line_diff(lines1, lines2)
        # end = time.perf_counter()


if __name__ == "__main__":
    main()
