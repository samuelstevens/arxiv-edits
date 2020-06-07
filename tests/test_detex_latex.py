from arxivedits.detex import latex


def test_find_pair():
    text = r"{}"
    assert latex.find_pair("{", "}", text) == (1, None)


def test_find_pair_with_space():
    text = r"{ }"
    assert latex.find_pair("{", "}", text) == (2, None)


def test_nested_pair():
    text = r"{{}}"
    assert latex.find_pair("{", "}", text) == (3, None)


def test_escaped_pair():
    text = r"{\}}"
    assert latex.find_pair("{", "}", text) == (3, None)


def test_escaped_escaped_pair():
    text = r"{{}\\}"
    assert latex.find_pair("{", "}", text) == (5, None)


def test_find_pair_with_spaces():
    text = "input hello should live"
    assert latex.find_pair(" ", " ", text) == (11, None)


def test_empty():
    text = ""
    assert latex.remove_tag(r"\footnote", text) == ""


def test_with_spaces():
    text = "\\input hello should live"
    assert latex.remove_tag(r"\input", text, braces=[" ", " "]) == "should live"


def test_removing_punct():
    text = "this moon \\citep{hello}, should live"
    assert latex.remove_tag(r"\citep", text) == "this moon , should live"


def test_no_tag_found_no_text():
    text = r"""
\begin{document}
\end{document}
"""

    assert latex.remove_tag(r"\footnote", text) == text


def test_no_tag_found():
    text = r"""
\begin{document}
This is an example document with no matching tags to find or remove.
\end{document}
"""

    assert latex.remove_tag(r"\footnote", text) == text


def test_one_tag():
    text = r"\footnote{document}"

    assert latex.remove_tag(r"\footnote", text) == ""


def test_with_brackets():
    text = r"\citep[hello there]{document}"

    assert latex.remove_tag(r"\citep", text) == ""


def test_with_multiple():
    text = r"\setcounter{figure}{document}"

    assert latex.remove_tag(r"\setcounter", text) == ""


def test_with_multiple_and_extra():
    text = r"\setcounter{figure}{document}{something else}"

    assert latex.remove_tag(r"\setcounter", text) == "{something else}"


def test_with_bigger_tag():
    text = r"\citepro{document}"

    assert latex.remove_tag(r"\citep", text) == text


def test_commas():
    text = r"Jack has considered this partial Hamiltonian, and has shown that by eliminating both the molecular and high-energy atomic fields from the evolution using a standard interaction picture approach for initially uncoupled fields , one obtains the master equation term"

    assert latex.remove_tag(r"\citep", text) == text


def test_commas_with_tag():
    text = r"""The dominant loss process affecting ultracold gaseous alkali metal systems is inelastic three-body recombination \cite{Moerdijk1996a,Wieman1997a,Dalibard1999a,Esry1999a}, a process characterised by collisional events involving three atoms leading to the creation of a single two-atom molecule (a dimer)."""

    output = r"""The dominant loss process affecting ultracold gaseous alkali metal systems is inelastic three-body recombination , a process characterised by collisional events involving three atoms leading to the creation of a single two-atom molecule (a dimer)."""
    assert latex.remove_tag(r"\cite", text) == output


def test_one_tag_with_braces():
    text = r"\footnote{hello there{document}}"

    assert latex.remove_tag(r"\footnote", text) == ""


def test_one_tag_with_braces_and_text():
    text = r"\footnote{hello} hi"

    assert latex.remove_tag(r"\footnote", text) == " hi"


def test_one_tag_with_braces_and_newline_text():
    text = "\\footnote{hello}\nhi\nhey"

    assert latex.remove_tag(r"\footnote", text) == "\nhi\nhey"


def test_typical_doc():
    text = r"""\footnote{hello there}
This is an example document with no matching tags to find or remove.\footnote{{hello there}}"""

    output = r"""
This is an example document with no matching tags to find or remove."""

    assert latex.remove_tag(r"\footnote", text) == output


def test_clean():
    initial_tex = r"""\section{\label{sec:results}Results}
\subsection{\label{subsec:phase_diag}Phase diagram}
We start by discussing the $0-\pi$ transition line, by comparison to
the numerical renormalization group (NRG) data by Bauer 
et al.\cite{NRG_spectral_Bauer}. Fig. \ref{fig:phase-diag} shows the 
extension to smaller gaps $\Delta$ values of the phase diagram obtained 
with unrenormalized local superconducting states for infinite gap 
(Fig. \ref{fig:phase-diag-inf})."""

    expected_text = r"""
\section{# Results}


\section{## Phase diagram}

We start by discussing the [MATH] transition line, by comparison to
the numerical renormalization group (NRG) data by Bauer 
et al.[CITATION]. Fig. [REF] shows the 
extension to smaller gaps [MATH] values of the phase diagram obtained 
with unrenormalized local superconducting states for infinite gap 
(Fig. [REF])."""

    assert latex.clean(initial_tex) == expected_text


def test_end_of_doc():
    initial_tex = r"""
\begin{document}
This is an example document with no matching tags to find or remove.
\end{document}
some more stuff behind it.
"""
    expected_text = r"""
This is an example document with no matching tags to find or remove.
"""

    assert latex.clean(initial_tex) == expected_text
