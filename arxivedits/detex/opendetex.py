"""
Exports detex_file(), which extracts text using `opendetex` and extensive preprocessing.
"""

import subprocess
import re
import logging

from arxivedits.detex import latex
from arxivedits.detex.constants import INLINE_MATH_TAG, ACKNOWLEDGEMENT_PATTERN
from arxivedits.structures import Result


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
    text = text.replace("noun", INLINE_MATH_TAG)
    text = text.replace("verbs", INLINE_MATH_TAG)

    # now we can put noun and verb back into the text.
    text = text.replace(TMP_NOUN_TAG, "noun")
    text = text.replace(TMP_VERB_TAG, "verbs")

    # (?:\[MATH\](?:\s|\d|\.|=|\(|\))+)+\[MATH\]
    regexp = (
        r"(?:"
        + re.escape(INLINE_MATH_TAG)
        + r"(?:\s|\d|=|\(|\))+)+"
        + re.escape(INLINE_MATH_TAG)
    )
    text = re.sub(regexp, INLINE_MATH_TAG, text)

    # chops off everything before the abstract
    start_abstract = text.find("Abstract")
    if start_abstract >= 0:
        text = text[start_abstract + len("Abstract") :]

    # chop off everything after acknowledgements
    acknowledgement_matches = list(ACKNOWLEDGEMENT_PATTERN.finditer(text))
    if acknowledgement_matches:
        text = text[: acknowledgement_matches[-1].start()]

    # turns multiple blank lines into one
    text = re.sub(r"\n(\s*\n)+", "\n\n", text)

    # removes tabs
    text = re.sub(r"\t+", " ", text, flags=re.MULTILINE)

    # removes multiple spaces
    text = re.sub(r" +", " ", text, flags=re.MULTILINE)

    return text


def detex(text: str) -> Result[str]:
    """
    opendetex (https://github.com/pkubowicz/opendetex), installed via homebrew (brew install detex)
    """

    try:
        text = preprocess(text)

        text = subprocess.run(
            ["detex", "-r"], text=True, input=text, capture_output=True
        ).stdout

        text = postprocess(text)

        return text
    except AttributeError:
        return ValueError(
            f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes)."
        )


def detex_file(inputfile: str, outputfile: str) -> None:
    """
    Takes a .tex file (inputfile) and extracts text, writes it to outputfile.
    """
    with open(inputfile, "r") as fin:
        with open(outputfile, "w") as fout:
            content = fin.read()

            detexed = detex(content)

            if isinstance(detexed, Exception):
                logging.warning(f"Can't detex {outputfile}: {detexed}")
            else:
                fout.write(detexed)


if __name__ == "__main__":

    test = r"""
\tableofcontents
\newpage

\lstdefinelanguage[bzr]{c++}
 {basicstyle=\scriptsize,
    morekeywords={node, returns, let, tel, peId, peid,  int,  var, contract,
      assume, enforce, with, bool, *, +, if, then , else, hwParam,
      func, main, and, not, until, state, do, true, false, automaton, end},  
 }

 \lstdefinelanguage{idl}
 {
  basicstyle=\scriptsize,
  morekeywords={in, out, interface}
 }
"""

    print(detex(test))
