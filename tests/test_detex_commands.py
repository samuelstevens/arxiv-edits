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

