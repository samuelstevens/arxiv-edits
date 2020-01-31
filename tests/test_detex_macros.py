from arxivedits.detex import macros


def test_command_with_args():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by #1 and #2""",
        arg_num=2,
        default_arg=None,
    )

    assert command.result(["John Doe", "Andrea Smith"]) == (
        r"This is the Wikibook about LaTeX supported by John Doe and Andrea Smith",
        None,
    )


def test_command_with_default_args():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"This is the Wikibook about LaTeX supported by #1 and #2",
        arg_num=2,
        default_arg="Wikimedia",
    )

    assert command.result(["John Doe"]) == (
        r"This is the Wikibook about LaTeX supported by Wikimedia and John Doe",
        None,
    )


def test_command_with_default_overrriden():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by #1 and #2""",
        arg_num=2,
        default_arg="Wikimedia",
    )

    assert command.result(["John Doe", "Andrea Smith"]) == (
        r"This is the Wikibook about LaTeX supported by John Doe and Andrea Smith",
        None,
    )


def test_command_with_default_with_braces():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by {#1} and {#2}""",
        arg_num=2,
        default_arg="Wikimedia",
    )

    assert command.result(["John Doe"]) == (
        r"This is the Wikibook about LaTeX supported by Wikimedia and John Doe",
        None,
    )


def test_get_args():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by {#1} and {#2}""",
        arg_num=2,
        default_arg=None,
    )

    text = "\\item \\wbalTwo{John Doe}{Anthea Smith}\n"

    assert macros.get_args(text, text.find("{"), command) == (
        38,
        ["John Doe", "Anthea Smith"],
    )


def test_get_args_with_overriden_default():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by {#1} and {#2}""",
        arg_num=2,
        default_arg="Wikimedia",
    )

    text = "\\item \\wbalTwo[John Doe]{Anthea Smith}\n"

    assert macros.get_args(text, text.find("["), command) == (
        38,
        ["John Doe", "Anthea Smith"],
    )


def test_get_args_with_default():
    command = macros.LatexCommand(
        r"\wbalTwo",
        r"This is the Wikibook about LaTeX supported by {#1} and {#2}",
        arg_num=2,
        default_arg="Wikimedia",
    )

    text = "\\item \\wbalTwo{Anthea Smith}\n"

    assert macros.get_args(text, text.find("{"), command) == (28, ["Anthea Smith"])


def test_no_macros():
    original_tex = r"""

\begin{itemize}
\item \wbal
\item \wbalsup{lots of users!}
\end{itemize}
"""
    assert macros.process(original_tex) == original_tex


def test_standard():
    original_tex = r"""
\newcommand{\wbal}{The Wikibook about \LaTeX}

\begin{itemize}
\item \wbal
\item \wbalsup{lots of users!}
\end{itemize}
"""
    expected_tex = r"""


\begin{itemize}
\item The Wikibook about \LaTeX
\item \wbalsup{lots of users!}
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_no_usage():
    original_tex = r"""
\newcommand{\wbal}{The Wikibook about \LaTeX}

\begin{itemize}
\item \wbalsup{lots of users!}
\end{itemize}
"""
    expected_tex = r"""


\begin{itemize}
\item \wbalsup{lots of users!}
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_args():
    original_tex = r"""
\newcommand{\wbalsup}[1] {
This is the Wikibook about LaTeX 
supported by #1}

\begin{itemize}
\item \wbalsup{lots of users!}
\end{itemize}
"""
    expected_tex = r"""


\begin{itemize}
\item This is the Wikibook about LaTeX 
supported by lots of users!
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_multiple_args():
    original_tex = r"""
\newcommand{\wbalsup}[1] {
  This is the Wikibook about LaTeX
  supported by #1}
\newcommand{\wbalTwo}[2] {
  This is the Wikibook about LaTeX
  supported by #1 and #2}
% in the document body:
\begin{itemize}
\item \wbalsup{Wikimedia}
\item \wbalsup{lots of users!}
\item \wbalTwo{John Doe}{Anthea Smith}
\end{itemize}
"""
    expected_tex = r"""


% in the document body:
\begin{itemize}
\item This is the Wikibook about LaTeX
  supported by Wikimedia
\item This is the Wikibook about LaTeX
  supported by lots of users!
\item This is the Wikibook about LaTeX
  supported by John Doe and Anthea Smith
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_args_with_braces():
    original_tex = r"""
\newcommand{\wbalsup}[1] {
  This is the Wikibook about LaTeX
  supported by {#1}}
\newcommand{\wbalTwo}[2] {
  This is the Wikibook about LaTeX
  supported by {#1} and {#2}}
% in the document body:
\begin{itemize}
\item \wbalsup{Wikimedia}
\item \wbalsup{lots of users!}
\item \wbalTwo{John Doe}{Anthea Smith}
\end{itemize}
"""
    expected_tex = r"""


% in the document body:
\begin{itemize}
\item This is the Wikibook about LaTeX
  supported by Wikimedia
\item This is the Wikibook about LaTeX
  supported by lots of users!
\item This is the Wikibook about LaTeX
  supported by John Doe and Anthea Smith
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_default():
    original_tex = r"""
\newcommand{\wbalTwo}[2][Wikimedia]{
  This is the Wikibook about LaTeX
  supported by {#1} and {#2}!}
% in the document body:
\begin{itemize}
\item \wbalTwo{John Doe}
\item \wbalTwo[lots of users]{John Doe}
\end{itemize}
"""

    expected_tex = r"""

% in the document body:
\begin{itemize}
\item This is the Wikibook about LaTeX
  supported by Wikimedia and John Doe!
\item This is the Wikibook about LaTeX
  supported by lots of users and John Doe!
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_with_space():
    original_tex = r"""
\newcommand {\ket}[1]{|{#1}\rangle}

\ket{hello}
"""

    expected_tex = r"""


|hello\rangle
"""
    assert macros.process(original_tex) == expected_tex


def test_with_non_letters():
    original_tex = r"""
\newcommand{\Pr@}{\operatorname{Pr}}

\Pr@
"""

    expected_tex = r"""


\operatorname{Pr}
"""
    assert macros.process(original_tex) == expected_tex


def test_with_no_braces():
    original_tex = r"""
\newcommand\name{output}
\name
"""

    expected_tex = r"""

output
"""
    assert macros.process(original_tex) == expected_tex


def test_with_math():
    original_tex = r"""
\newcommand{\bnd}{\mathscr{B}un_X^{k,l}(n,d)}
$\bnd$
"""

    expected_tex = r"""

$\mathscr{B}un_X^{k,l}(n,d)$
"""
    assert macros.process(original_tex) == expected_tex