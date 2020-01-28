from tex import remove_tag, find_pair, line_starts_with
from typing import List
import string


def test_find_pair():
    text = r"{}"
    assert find_pair("{", "}", text) == 1


def test_find_pair_with_space():
    text = r"{ }"
    assert find_pair("{", "}", text) == 2


def test_nested_pair():
    text = r"{{}}"
    assert find_pair("{", "}", text) == 3


def test_finding_with_spaces():
    text = "input hello should live"
    assert find_pair(" ", " ", text) == 11


def test_empty():
    text = ""
    assert remove_tag(r"\footnote", text) == ""


def test_with_spaces():
    text = "\\input hello should live"
    assert remove_tag(r"\input", text, braces=[" ", " "]) == "should live"


def test_removing_punct():
    text = "this moon \\citep{hello}, should live"
    assert remove_tag(r"\citep", text) == "this moon, should live"


def test_no_tag_found_no_text():
    text = r"""
\begin{document}
\end{document}
"""

    assert remove_tag(r"\footnote", text) == text


def test_no_tag_found():
    text = r"""
\begin{document}
This is an example document with no matching tags to find or remove.
\end{document}
"""

    assert remove_tag(r"\footnote", text) == text


def test_one_tag():
    text = r"\footnote{document}"

    assert remove_tag(r"\footnote", text) == ""


def test_with_brackets():
    text = r"\citep[hello there]{document}"

    assert remove_tag(r"\citep", text) == ""


def test_with_multiple():
    text = r"\setcounter{figure}{document}"

    assert remove_tag(r"\setcounter", text) == ""


def test_with_multiple_and_extra():
    text = r"\setcounter{figure}{document}{something else}"

    assert remove_tag(r"\setcounter", text) == "{something else}"


def test_with_bigger_tag():
    text = r"\citepro{document}"

    assert remove_tag(r"\citep", text) == text


def test_commas():
    text = r"Jack has considered this partial Hamiltonian, and has shown that by eliminating both the molecular and high-energy atomic fields from the evolution using a standard interaction picture approach for initially uncoupled fields , one obtains the master equation term"

    assert remove_tag(r"\citep", text) == text


def test_commas_with_tag():
    text = r"""The dominant loss process affecting ultracold gaseous alkali metal systems is inelastic three-body recombination \cite{Moerdijk1996a,Wieman1997a,Dalibard1999a,Esry1999a}, a process characterised by collisional events involving three atoms leading to the creation of a single two-atom molecule (a dimer)."""

    output = r"""The dominant loss process affecting ultracold gaseous alkali metal systems is inelastic three-body recombination, a process characterised by collisional events involving three atoms leading to the creation of a single two-atom molecule (a dimer)."""
    assert remove_tag(r"\cite", text) == output


def test_one_tag_with_braces():
    text = r"\footnote{hello there{document}}"

    assert remove_tag(r"\footnote", text) == ""


def test_one_tag_with_braces_and_text():
    text = r"\footnote{hello} hi"

    assert remove_tag(r"\footnote", text) == " hi"


def test_one_tag_with_braces_and_newline_text():
    text = "\\footnote{hello}\nhi\nhey"

    assert remove_tag(r"\footnote", text) == "\nhi\nhey"


def test_typical_doc():
    text = r"""\footnote{hello there}
This is an example document with no matching tags to find or remove.\footnote{{hello there}}"""

    output = r"""
This is an example document with no matching tags to find or remove."""

    assert remove_tag(r"\footnote", text) == output


def test_line():
    text = "hello"
    assert line_starts_with("hel", text, 5) == True


def test_lines():
    text = """
hello
nah
    """
    assert line_starts_with("hel", text, 8) == False


def test_lines_true():
    text = """
hello
nah
    """
    assert line_starts_with("na", text, 8) == True


def split_on_tag(tag: str, text: str, offset: int = 0) -> List[str]:
    if tag in text[offset:]:
        nextsentence = text.index(tag, offset) + len(tag)

        if nextsentence + 1 >= len(text):
            return [text]

        # if the next letter after the tag is uppercase, split.
        if text[nextsentence + 1] in string.ascii_uppercase:
            return [
                text[:nextsentence],
                *split_on_tag(tag, text[nextsentence:].lstrip()),
            ]

        # else try and split further on
        return split_on_tag(tag, text, nextsentence + 1)

    return [text]


def test_split():
    tag = "[EQUATION]"

    text = r"It is simply a unitary transformation of the system, [EQUATION] We use the pseudo-spectral method to solve the Schrodinger equation in the comoving box."

    output = [
        "It is simply a unitary transformation of the system, [EQUATION]",
        "We use the pseudo-spectral method to solve the Schrodinger equation in the comoving box.",
        "Let [MATH] be the kinetic energy operator ([MATH] in Fourier space) and [MATH] the potential operator([MATH] in real space).",
    ]

    for i, r in enumerate(split_on_tag(tag, text)):
        assert r == output[i]


def test_split2():
    tag = "[EQUATION]"

    text = r"The evolution is then split into [EQUATION] On the other hand, we need to consider the non-commutative relation between [MATH] and [MATH], where [EQUATION] [EQUATION] It follows that we obtain, to the second order accuracy, [EQUATION] which will be adopted to advance the time steps."

    output = [
        "The evolution is then split into [EQUATION]",
        "On the other hand, we need to consider the non-commutative relation between [MATH] and [MATH], where [EQUATION] [EQUATION]",
        "It follows that we obtain, to the second order accuracy, [EQUATION] which will be adopted to advance the time steps.",
    ]

    for i, r in enumerate(split_on_tag(tag, text)):
        assert r == output[i]

