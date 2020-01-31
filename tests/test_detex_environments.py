from arxivedits.detex import environments


def test_line_starts_with():
    text = r"""
hello there
oh hi
who are you?
"""

    assert environments.line_starts_with("hello", text, 9) == True


def test_get_env_name_standard():
    text = r"\begin{document}"
    expected_env = "document"

    assert environments.get_env_name(text) == expected_env


def test_get_env_name_with_star():
    text = r"\begin{figure*}"
    expected_env = "figure*"

    assert environments.get_env_name(text) == expected_env


def test_figure():
    original_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}
\begin{figure}
some figure.
\end{figure}
\end{document}
"""
    expected_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}

\end{document}
"""
    assert environments.process(original_tex) == expected_tex


def test_no_env():
    original_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}


\end{document}
"""
    expected_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}


\end{document}
"""
    assert environments.process(original_tex) == expected_tex


def test_equations():
    original_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}
\begin{equation}

$ some math here $

\end{equation}
\end{document}
"""
    expected_tex = r"""
\begin{document}
\begin{abstract}
some text.
\end{abstract}
[EQUATION]
\end{document}
"""
    assert environments.process(original_tex) == expected_tex
