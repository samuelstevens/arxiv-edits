"""
Quality filters for documents, document pairs and sentences
"""

import functools, re, string

from arxivedits.detex.constants import (
    INLINE_MATH_TAG,
    BLOCK_MATH_TAG,
    CITE_TAG,
    REF_TAG,
)

from arxivedits import util, data, preprocess


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


def doc_filter(arxivid: str, version: int) -> bool:
    """
    Checks if the document uses the harvmac package.
    """

    input_harvmac_pattern = re.compile(r"^[^%]*\\input harvmac")

    with open(data.latex_path(arxivid, version)) as file:
        for line in file:
            if input_harvmac_pattern.match(line):
                return False

    return True


def doc_pair_filter(arxivid: str, v1: int, v2: int) -> bool:
    """
    Checks if there are more than 5000 pairs where both sentences have 3+ [MATH] tags.
    """
    with_3_plus_v1 = 0
    with_3_plus_v2 = 0

    pgs1 = data.get_paragraphs(arxivid, v1)
    if isinstance(pgs1, Exception):
        return False

    pgs2 = data.get_paragraphs(arxivid, v2)
    if isinstance(pgs2, Exception):
        return False

    lines1 = util.paragraphs_to_lines(pgs1)
    lines2 = util.paragraphs_to_lines(pgs2)

    for line in lines1:
        sent = preprocess.preprocess_sent(line)
        words = util.sent_to_words(sent)
        if len([word for word in words if word in (INLINE_MATH_TAG)]) >= 3:
            with_3_plus_v1 += 1

    for line in lines2:
        sent = preprocess.preprocess_sent(line)
        words = util.sent_to_words(sent)
        if len([word for word in words if word in (INLINE_MATH_TAG)]) >= 3:
            with_3_plus_v2 += 1

    return with_3_plus_v1 * with_3_plus_v2 > 5000
