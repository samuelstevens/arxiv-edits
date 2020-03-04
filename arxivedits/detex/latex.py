import string
import re
from typing import List
import logging

from arxivedits import structures
from arxivedits.detex import macros, environments, commands
from arxivedits.detex.constants import (
    BLOCK_MATH_PATTERN,
    BLOCK_MATH_TAG,
    MATH_TAG,
    INLINE_MATH_PATTERN,
    SECTION_PATTERNS,
    BAD_TAGS,
    # citations
    CITE_TAGS_REMOVE,
    CITE_TAGS_REPLACE,
    CITE_TAG,
    # references
    REF_TAGS,
    REF_TAG,
)


def find_pair(
    opening_char: str, closing_char: str, text: str, start: int = 0
) -> structures.Go[int]:
    """
    Takes a pair of characters and text and finds the location of the ending char.

    `"{ {} }"` would return the location of the second `'}'`.
    """
    # go to first start_char
    pos = text.find(opening_char, start)

    if pos < 0:
        return len(text), ValueError(f"substring {opening_char} not found.")

    if opening_char == closing_char:
        pos = text.find(opening_char, pos + 1)

        if pos < 0:
            return len(text), ValueError(f"No matching {closing_char}.")

        return pos, None

    count = 0

    while pos < len(text):
        if text[pos] == opening_char:
            count += 1
        elif text[pos] == closing_char:
            count -= 1

        if count == 0:
            return pos, None

        pos += 1

    return len(text), ValueError(f"No matching {closing_char}.")


def strip_abstract(text: str) -> str:
    text = text.replace(r"\begin{abstract}", "# Abstract")

    text = text.replace(r"\end{abstract}", "")

    return text


def clean(initial_tex: str) -> str:
    """
    Preprocesses a LaTeX file for use with `opendetex`.
    """

    text = remove_comments(initial_tex)

    text = macros.process(text)

    text = environments.process(text)

    text = commands.process(text)

    # removes additional macros and stuff
    start_doc = text.find(r"\begin{document}")
    if start_doc >= 0:
        text = text[start_doc + len(r"\begin{document}") :]

    # chops off end of document
    end_doc = text.find(r"\end{document}")
    if end_doc >= 0:
        text = text[:end_doc]

    # chop off bibliography
    start_bib = text.find(r"\thebibliography")
    if start_bib >= 0:
        text = text[:start_bib]

    text = strip_abstract(text)

    text = removeBadMath(text)

    for tag in BAD_TAGS:
        text = remove_tag(tag, text)

    for tag in CITE_TAGS_REMOVE:
        text = remove_tag(tag, text)

    for tag in CITE_TAGS_REPLACE:
        text = remove_tag(tag, text, replace=CITE_TAG)

    for tag in REF_TAGS:
        text = remove_tag(tag, text, replace=REF_TAG)

    # change $$...$$ to [EQUATION]
    # needs to go first so that $$...$$ isn't turned to $[MATH]$
    text = BLOCK_MATH_PATTERN.sub(BLOCK_MATH_TAG + " ", text)

    # change $...$ to [MATH]
    text = INLINE_MATH_PATTERN.sub(MATH_TAG + " ", text)

    # change [MATH] [MATH]  [MATH] to [MATH]
    # (\[MATH\] *)+\[MATH\]
    regexp = r"(?:" + re.escape(MATH_TAG) + r" *)+" + re.escape(MATH_TAG)
    # print("before:", re.findall(regexp, text))
    text = re.sub(regexp, MATH_TAG, text)
    # print("after:", re.findall(regexp, text))

    # removes blank lines before [EQUATION]
    regexp = r"\n\n+\[EQUATION\]"
    text = re.sub(regexp, f"\n{BLOCK_MATH_TAG}", text)

    # removes blank lines after [EQUATION]
    regexp = r"\[EQUATION\]( ?\n)( ?\n)+"
    text = re.sub(regexp, f"{BLOCK_MATH_TAG}\n", text)

    # changes \section{something} to \section{# something}
    for i, pattern in enumerate(SECTION_PATTERNS):
        replacement_heading = r"\n\\section{" + "#" * (i + 1) + r" \1}\n"
        text = pattern.sub(replacement_heading, text)

    # removes multiple spaces
    text = re.sub(r" +", " ", text, flags=re.MULTILINE)

    #     lines = text.split("\n")

    #     # joins all lines that end with <non-whitespace>%
    #     i = 0
    #     while i < len(lines):
    #         if MACRO_COMMENT_PATTERN.search(lines[i]):
    #             lines[i] = lines[i][:-1]
    #             lines[i] += lines[i + 1]
    #             lines[i + 1] = ""
    #             i += 1

    #         i += 1

    #     # removes lines with \authorblock
    #     lines = [line for line in lines if not line.lstrip().startswith(r"\authorblock")]

    #     # changes \citet{something} to [CITATION]
    #     text = EXTRACT_CITATION_PATTERN.sub(CITE_TAG, text)

    #     text = GRAPHICS_PATTERN.sub("", text)

    #

    #     text = remove_tag(r"\input", text, braces=[" ", " "])

    #     if not basic:
    #         # remove \label{...}
    #         text = remove_tag(r"\label", text)

    #     # turns multiple blank lines into one
    #     text = re.sub(r"\n(\s*\n)+", "\n\n", text)

    #     start_doc = text.find(r"\begin{document}")

    #     if start_doc >= 0:
    #         text = text[start_doc:]

    #     # removes multiple spaces
    #     text = re.sub(r" +", " ", text, flags=re.MULTILINE)

    #     # removes spaces at the start of a line
    #     text = re.sub("^ ", "", text, flags=re.MULTILINE)

    #     return text

    return text


def remove_comments(text: str) -> str:
    """
    Removes comments (any % not preceded by a \\ until the end of the line).
    """
    return re.sub(r"(?<!\\)%.*$", "", text, flags=re.MULTILINE)


def remove_tag(tag: str, text: str, braces=None, replace="") -> str:
    """
    Removes tags like `\\footnote` or `\\def` from a string by using `find_pair()` to handle nested braces. This is better than guessing if a greedy regex will work.
    """

    if not braces:
        braces = ["{", "}"]

    tags_with_extra_braces = [r"\setcounter"]

    string_builder: List[str] = []

    end_pos = 0
    current_pos = 0
    tags_found = 0

    while current_pos < len(text):
        start_pos = text.find(tag, current_pos)

        if start_pos < 0:
            string_builder.append(text[end_pos:])
            break

        # if we have the wrong tag, text[start_pos+len(tag)] won't be {, [, etc.
        if text[start_pos + len(tag)] in string.ascii_letters:
            current_pos = start_pos + 1
            continue

        string_builder.append(text[end_pos:start_pos])
        string_builder.append(replace)
        tags_found += 1

        end_of_tag, err = find_pair(braces[0], braces[1], text, start_pos)

        if isinstance(end_of_tag, Exception):
            logging.warning("Error in remove tag.")
            logging.warning(end_of_tag)
            break

        if tag in tags_with_extra_braces:
            end_of_tag, err = find_pair(braces[0], braces[1], text, end_of_tag + 1)

        if isinstance(err, Exception):
            logging.warning("Error in remove tag.")
            logging.warning(err)
            break

        end_pos = end_of_tag + 1  # +1 is for getting past }

        if end_pos >= len(text):
            break

        current_pos = end_pos

    text = "".join(string_builder)

    return text


def removeBadMath(content: str) -> str:
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
