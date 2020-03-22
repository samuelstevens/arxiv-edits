"""
Handles math in .tex documents.
"""

import re

from arxivedits.detex.constants import (
    BLOCK_MATH_TAG,
    INLINE_MATH_TAG,
)


# $$...$$
BLOCK_MATH_PATTERN = re.compile(r"(?<!\\)\$\$.*?[^\\]\$\$", re.MULTILINE | re.DOTALL)


# $...$
INLINE_MATH_PATTERN = re.compile(r"(?<!\\)\$.*?[^\\]\$", re.MULTILINE | re.DOTALL)


def _remove_bad_math(content: str) -> str:
    r"""
    Changes modern LaTeX sequences such as `\( \)` and `\[ \]` to `$ $`. 
    
    Written by Chenhao Tan, modified by Sam Stevens.
    """
    # result is a list of lines
    result = []
    pos = 0

    while pos < len(content) - 1:
        # if the current 2 chars are \(
        if content[pos : pos + 2] == "\\(":
            # if the previous character was not \ (so the entire sequence is NOT "\\(" )
            if not (pos > 0 and content[pos - 1] == "\\"):
                # add a $ for Latex math
                result.append(" $ ")
                # go past these two chars
                pos += 2
                # start loop again
                continue

        # if the 2 current chars are \(
        if content[pos : pos + 2] == "\\)":
            # making sure the slash isn't escaped
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $ ")
                pos += 2
                continue

        # if the 2 current chars are \[
        if content[pos : pos + 2] == "\\[":
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $$ ")
                pos += 2
                continue

        # if the 2 current chars are \]
        if content[pos : pos + 2] == "\\]":
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $$ ")
                pos += 2
                continue

        # if this position isn't one of those char sequences, append a single character
        result.append(content[pos])
        pos += 1

    # sometimes you'll end up without the last char.
    if pos < len(content):
        result.append(content[pos])

    # rejoin the string
    return "".join(result)


def _remove_math(text: str, pattern: re.Pattern, replace_tag: str) -> str:
    text = _remove_bad_math(text)

    pos = 0
    string_builder = []

    while pos < len(text):
        math_match = pattern.search(text, pos=pos)

        if math_match:
            start, end = math_match.span()
            equation = math_match.group(0)
            replace_tag = replace_tag
        else:
            break

        string_builder.append(text[pos:start])
        string_builder.append(replace_tag)

        punc_match = re.search(r"[^.]\.\s*\$", equation)
        capital_match = re.search(r"^\s+[A-Z]", text[end:])

        if punc_match and capital_match:
            string_builder.append(".")

        pos = end

    string_builder.append(text[pos:])

    return "".join(string_builder)


def remove_inline_math(text: str) -> str:
    return _remove_math(text, INLINE_MATH_PATTERN, INLINE_MATH_TAG)


def remove_block_math(text: str) -> str:
    return _remove_math(text, BLOCK_MATH_PATTERN, BLOCK_MATH_TAG)


def consecutive_math(text: str) -> str:
    regexp = r"(?:" + re.escape(INLINE_MATH_TAG) + r"\s*)+" + re.escape(INLINE_MATH_TAG)
    return re.sub(regexp, INLINE_MATH_TAG, text)
