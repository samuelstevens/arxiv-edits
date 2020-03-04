"""
Exports detex_file(), which extracts text using `opendetex` and extensive preprocessing.
"""

import subprocess, re
import logging

from arxivedits.detex import latex
from arxivedits.detex.constants import MATH_TAG
from arxivedits import structures


TMP_NOUN_TAG = "[TMPNOUN]"
TMP_VERB_TAG = "[TMPVERB]"


def preprocess(text: str) -> str:
    """
    Preprocesses text for `opendetex`.
    """

    text = latex.clean(text)

    # replaces noun and verb with some temp tags that are unlikely to show up in a latex document.
    text = text.replace("noun", TMP_NOUN_TAG)
    text = text.replace("verbs", TMP_VERB_TAG)

    return text


def postprocess(text: str) -> str:
    """
    Does some minor post processing on `opendetex`'s output.
    """
    # replaces any occurence of noun, verb with [MATH]. The only occurences of noun and verb will be from opendetex.
    text = text.replace("noun", MATH_TAG)
    text = text.replace("verbs", MATH_TAG)

    # now we can put noun and verb back into the text.
    text = text.replace(TMP_NOUN_TAG, "noun")
    text = text.replace(TMP_VERB_TAG, "verbs")

    # (?:\[MATH\](?:\s|\d|\.|=|\(|\))+)+\[MATH\]
    regexp = (
        r"(?:" + re.escape(MATH_TAG) + r"(?:\s|\d|\.|=|\(|\))+)+" + re.escape(MATH_TAG)
    )
    text = re.sub(regexp, MATH_TAG, text)

    # chops off everything before the abstract
    start_abstract = text.find("Abstract")
    if start_abstract >= 0:
        text = text[start_abstract + len("Abstract") :]

    # turns multiple blank lines into one
    text = re.sub(r"\n(\s*\n)+", "\n\n", text)

    # removes multiple spaces
    text = re.sub(r" +", " ", text, flags=re.MULTILINE)

    return text


def detex(text: str) -> structures.Go[str]:
    """
    opendetex (https://github.com/pkubowicz/opendetex), installed via homebrew (brew install detex)
    """

    try:
        text = preprocess(text)

        text = subprocess.run(
            ["detex", "-r"], text=True, input=text, capture_output=True
        ).stdout

        text = postprocess(text)

        return text, None
    except AttributeError:
        return (
            "",
            ValueError(
                f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes)."
            ),
        )


def detex_file(inputfile, outputfile):
    """
    Takes a .tex file (inputfile) and extracts text, writes it to outputfile.
    """
    with open(inputfile, "r") as fin:
        with open(outputfile, "w") as fout:
            content = fin.read()

            detexed, err = detex(content)

            if err:
                logging.warning(err)

            fout.write(detexed)

