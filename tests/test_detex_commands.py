from arxivedits.detex import commands


def test_default_command():
    initial_tex = r"""{\setlength\arraycolsep{1pt} [EQUATION]}"""

    expected_tex = r"{ [EQUATION]}"

    assert commands.process(initial_tex) == expected_tex


def test_false_command():
    initial_tex = r"""{setlength\arraycolsep{1pt} [EQUATION]}"""

    expected_tex = initial_tex

    assert commands.process(initial_tex) == expected_tex


def test_setlength():
    initial_tex = r"""{\setlength\arraycolsep{1pt} [EQUATION]}"""

    expected_tex = (("", 27), None)

    assert commands.LengthParse(initial_tex, 1, "setlength") == expected_tex


def test_addtolength():
    initial_tex = r"""\addtolength{\mylength}{length}"""

    expected_tex = (("", 30), None)

    assert commands.LengthParse(initial_tex, 0, "addtolength") == expected_tex


def test_newtheorem():
    initial_tex = r"\newtheorem{theorem}{Theorem}"
    expected_tex = (("", len(initial_tex) - 1), None)
    assert commands.NewTheoremParse(initial_tex, 0, "newtheorem") == expected_tex


def test_newtheorem_with_middle_count():
    initial_tex = r"\newtheorem{tw}[theorem]{Theorem}"
    expected_tex = (("", len(initial_tex) - 1), None)
    assert commands.NewTheoremParse(initial_tex, 0, "newtheorem") == expected_tex


def test_newtheorem_with_end_count():
    initial_tex = r"\newtheorem{tw}{Theorem}[theorem]"
    expected_tex = (("", len(initial_tex) - 1), None)
    assert commands.NewTheoremParse(initial_tex, 0, "newtheorem") == expected_tex


def test_lst():
    initial_tex = r"""\lstdefinelanguage[bzr]{c++}
 {basicstyle=\scriptsize,
    morekeywords={node, returns, let, tel, peId, peid,  int,  var, contract,
      assume, enforce, with, bool, *, +, if, then , else, hwParam,
      func, main, and, not, until, state, do, true, false, automaton, end},  
}
"""
    expected_tex = (("", len(initial_tex) - 1), None)
    assert (
        commands.LstDefineLanguageParse(initial_tex, 0, "lstdefinelanguage")
        == expected_tex
    )


def test_lst_with_more_text():
    initial_tex = r"""\lstdefinelanguage[bzr]{c++}
 {basicstyle=\scriptsize,
    morekeywords={node, returns, let, tel, peId, peid,  int,  var, contract,
      assume, enforce, with, bool, *, +, if, then , else, hwParam,
      func, main, and, not, until, state, do, true, false, automaton, end},  
}

something else
"""
    expected_output = ""
    expected_err = None

    (output, pos), err = commands.LstDefineLanguageParse(
        initial_tex, 0, "lstdefinelanguage"
    )

    assert err == expected_err
    assert initial_tex[pos:] == "\n\nsomething else\n"


def test_lst_no_brackets():
    initial_tex = r"""\lstdefinelanguage{idl}
 {
  basicstyle=\scriptsize,
  morekeywords={in, out, interface}
 }

other stuff"""

    expected_output = ""
    expected_err = None

    (output, pos), err = commands.LstDefineLanguageParse(
        initial_tex, 0, "lstdefinelanguage"
    )

    assert err == expected_err
    assert initial_tex[pos:] == "\n\nother stuff"


r"""
\newtheorem{theorem}{Theorem} \newtheorem{tw}[theorem]{Theorem}
\newtheorem{stw}[theorem]{Proposition} \newtheorem{lem}[theorem]{Lemma}
\newtheorem{rem}[theorem]{Remark} \newtheorem{defi}[theorem]{Definition}
\newtheorem{definition}[theorem]{Definition} \newtheorem{corollary}[theorem]{Corollary}
"""
