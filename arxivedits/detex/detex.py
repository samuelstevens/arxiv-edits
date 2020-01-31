"""
Exports detex_file(), which extracts text using `opendetex` and extensive preprocessing.
"""

import subprocess

from arxivedits.detex import latex
from arxivedits import structures


def detex(text: str) -> structures.Go[str]:
    """
    opendetex (https://github.com/pkubowicz/opendetex), installed via homebrew (brew install detex)
    """

    mathtag = "[MATH]"
    verbtag = "[DOES]"

    tmp_nountag = "[TMPNOUN]"
    tmp_verbtag = "[TMPVERB]"

    text = latex.clean(text)

    text = text.replace("noun", tmp_nountag)
    text = text.replace("verbs", tmp_verbtag)

    try:
        text = subprocess.run(
            ["detex", "-r"], text=True, input=text, capture_output=True
        ).stdout

        text = text.replace("noun", mathtag)
        text = text.replace("verbs", verbtag)

        text = text.replace(tmp_verbtag, "noun")
        text = text.replace(tmp_nountag, "verbs")

        return text, None
    except AttributeError:
        return (
            "",
            ValueError(
                f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes)."
            ),
        )


def detex_file(inputfile, outputfile, clean=True):
    """
    Takes a .tex file (inputfile) and extracts text, writes it to outputfile.
    """
    with open(inputfile, "r") as fin:
        with open(outputfile, "w") as fout:
            content = fin.read()

            detexed, err = detex(content)

            if err:
                print(err)

            fout.write(detexed)
