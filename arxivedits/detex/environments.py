import re
import logging
from typing import List, Tuple, Optional

from arxivedits.detex.constants import BLOCK_MATH_TAG, INLINE_MATH_TAG


def line_starts_with(search: str, text: str, position: int) -> bool:
    if position < 0:
        position = 0
    if position > len(text) - len(search):
        position = len(text) - len(search)

    while position >= 0:
        if text[position] == "\n" or text[position] == "\r":
            break

        position -= 1

    # now text[position] is the first char in the line
    position += 1

    return text[position:].startswith(search)


def get_env_name(subtext: str) -> str:
    r"""
    Assumes subtext starts with `\begin{`
    """
    match = re.match(r"\\begin\{(.*?)\}", subtext)
    if not match:
        print("Couldn't find \\begin{ in %s", subtext[:20])
        return ""

    return match.group(1)


def process(text: str) -> str:
    """
    Removes bad environments and their contents like `\\begin{equation}` and `\\begin{table}` from text.
    """

    bad_environments = {
        "equation": BLOCK_MATH_TAG,
        "subequation": BLOCK_MATH_TAG,
        "eqnarray": BLOCK_MATH_TAG,
        "prop": None,
        "array": None,
        "figure": None,
        "align": BLOCK_MATH_TAG,  # same thing as eqnarray
        "table": None,
        "tabular": None,
        "math": INLINE_MATH_TAG,  # equivalent to $...$
        "matrix": None,
        "displaymath": BLOCK_MATH_TAG,  # equivalent to $$...$$
        "thebibliography": None,
        "keywords": None,  # typically not sentences.
        "alignat": None,  # sometimes math, but not always
        "multline": None,  # sometimes math, but not always
        "itemize": None,  # lists are mostly not full sentences.
        "tikzpicture": None,  # picture
        "keyword": None,
        "flushright": None,  # usually used to store keywords and equations
        "lstlisting": None,  # code environments
    }

    valid: List[Tuple[int, int, Optional[str]]] = []

    end_env = 0
    pos = 0
    while pos < len(text):
        start_env = text.find(r"\begin{", pos)

        if start_env < 0:
            valid.append((end_env, len(text), None))
            break

        env_name = get_env_name(text[start_env:])

        if (
            env_name in bad_environments or env_name[:-1] in bad_environments
        ):  # env_name[:-1] accounts for table*, figure*, etc.

            if env_name in bad_environments:
                replaced = bad_environments[env_name]
            else:
                replaced = bad_environments[env_name[:-1]]

            valid.append((end_env, start_env, replaced))

            end_env_command = r"\end{" + env_name + r"}"

            end_env = text.find(end_env_command, start_env + 1)

            if end_env < 0:
                logging.warning("Missing \\end for %s", end_env_command)
                end_env = len(text)

            end_env += len(end_env_command)

            pos = end_env
        else:
            pos = start_env + 1  # +1 gets past the initial .find()

    # process valid
    final = []
    for v in valid:
        final.append(text[v[0] : v[1]])
        replacement = v[2]
        if isinstance(replacement, str):
            final.append(replacement)

    return "".join(final)

