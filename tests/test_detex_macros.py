from arxivedits.detex import macros


def test_command_with_args():
    command = macros.LatexMacro(
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
    command = macros.LatexMacro(
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
    command = macros.LatexMacro(
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
    command = macros.LatexMacro(
        r"\wbalTwo",
        r"""This is the Wikibook about LaTeX supported by {#1} and {#2}""",
        arg_num=2,
        default_arg="Wikimedia",
    )

    assert command.result(["John Doe"]) == (
        r"This is the Wikibook about LaTeX supported by {Wikimedia} and {John Doe}",
        None,
    )


def test_parse_command():
    original_tex = r"""\newcommand{\wbal}{The Wikibook about \LaTeX}

\begin{itemize}
\item \wbal
\item \wbalsup{lots of users!}
\end{itemize}
"""
    expected_command = macros.LatexMacro(r"\wbal", r"The Wikibook about \LaTeX")

    parser = macros.NewCommandParser(original_tex, 0)

    result, err = parser.parse()
    actual_command, actual_pos = result

    assert actual_command == expected_command
    assert actual_pos == 44
    assert err is None


def test_parse_def():
    original_tex = r"""\def \name{\emph{sam}}

\name

\end{document}
"""
    expected_command = macros.LatexMacro(r"\name", r"\emph{sam}")

    parser = macros.DefParser(original_tex, 0)

    result, err = parser.parse()
    actual_command, actual_pos = result

    assert actual_command == expected_command
    assert actual_pos == 21
    assert err is None


def test_parse_def_with_symbol():
    original_tex = r"""\def \{{\emph{}

\{

\end{document}
"""
    expected_command = macros.LatexMacro(r"\{", r"\emph{")

    parser = macros.DefParser(original_tex, 0)

    result, err = parser.parse()
    actual_command, actual_pos = result

    assert actual_command == expected_command
    assert actual_pos == 14
    assert err is None


def test_get_args():
    command = macros.LatexMacro(
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
    command = macros.LatexMacro(
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
    command = macros.LatexMacro(
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
  supported by {Wikimedia}
\item This is the Wikibook about LaTeX
  supported by {lots of users!}
\item This is the Wikibook about LaTeX
  supported by {John Doe} and {Anthea Smith}
\end{itemize}
"""

    assert macros.process(original_tex) == expected_tex


def test_default():
    original_tex = r"""
\newcommand{\wbalTwo}[2][Wikimedia]{
  This is the Wikibook about LaTeX
  supported by #1 and #2!}
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


|{hello}\rangle
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


def test_multiline():
    original_tex = r"""
\documentclass{article}

\begin{document}

\newcommand{\name}[1][\emph{
    big
}]{\emph{else} #1}

\name

\end{document}
"""
    expected_tex = r"""
\documentclass{article}

\begin{document}



\emph{else} \emph{
    big
}

\end{document}
"""
    assert macros.process(original_tex) == expected_tex


def test_def():
    original_tex = r"""
\documentclass{article}

\begin{document}

\def \name{\emph{else}}

\name

\end{document}
"""
    expected_tex = r"""
\documentclass{article}

\begin{document}



\emph{else}

\end{document}
"""
    assert macros.process(original_tex) == expected_tex


def test_commented_command():
    original_tex = r"""
\newcommand{\mdot}{\mbox{M$_{\odot}$ yr$^{-1}$}}
\newcommand{\test}{Hi there!}

\test hello there \mdot\
\\mdot
"""
    expected_tex = r"""



Hi there! hello there \mbox{M$_{\odot}$ yr$^{-1}$}
\\mdot
"""

    assert macros.process(original_tex) == expected_tex


def test_robust_command():
    original_tex = r"""
\DeclareRobustCommand{\pder}[1]{%
  \@ifnextchar\bgroup{\@pder{#1}}{\@pder{}{#1}}}

\pder{hello}
"""

    expected_tex = r"""


\@ifnextchar\bgroup{\@pder{hello}}{\@pder{}{hello}}
"""

    assert macros.process(original_tex) == expected_tex


def test_chained_command():
    original_tex = r"""
\DeclareRobustCommand{\pder}[1]{%
  \@ifnextchar\bgroup{\@pder{#1}{#1}}}
\newcommand{\@pder}[2]{\frac{\partial #1}{\partial #2}}

\pder{hello}
"""

    expected_tex = r"""



\@ifnextchar\bgroup{\frac{\partial hello}{\partial hello}}
"""

    assert macros.process(original_tex) == expected_tex
