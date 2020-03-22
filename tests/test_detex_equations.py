from arxivedits.detex import equations


def test_equation():
    text = r"Given $$equation,$$ we aim to find a solution."

    expected = r"Given [EQUATION] we aim to find a solution."

    assert equations.remove_block_math(text) == expected
    assert equations.remove_block_math(expected) == expected


def test_equation_with_period():
    text = r"Given $$equation.$$ We aim to find a solution."

    expected = r"Given [EQUATION]. We aim to find a solution."

    assert equations.remove_block_math(text) == expected
    assert equations.remove_block_math(expected) == expected


def test_inline():
    text = r"Given a ring $R$ we denote by $Q(R)$ its quotient field and given a link $L\subset S^3$ we denote by $\nu L$ a (open) tubular neighborhood of $L$ in $S^3$."

    expected = r"Given a ring [MATH] we denote by [MATH] its quotient field and given a link [MATH] we denote by [MATH] a (open) tubular neighborhood of [MATH] in [MATH]."

    assert equations.remove_inline_math(text) == expected
    assert equations.remove_inline_math(expected) == expected


def test_inline_with_period():
    text = r"In the first case, we subtract the thing when $\Delta r<\Delta R.$ We then try again."

    expected = (
        r"In the first case, we subtract the thing when [MATH]. We then try again."
    )

    assert equations.remove_inline_math(text) == expected
    assert equations.remove_inline_math(expected) == expected


def test_inline_with_period_no_capital():
    text = r"In the first case, when $\Delta r<\Delta R.$ where something."

    expected = r"In the first case, when [MATH] where something."

    assert equations.remove_inline_math(text) == expected
    assert equations.remove_inline_math(expected) == expected


def test_inline_with_period_and_whitespace_inside():
    text = r"In the first case, we subtract the thing when $\Delta r<\Delta R    .$ We then try again."

    expected = (
        r"In the first case, we subtract the thing when [MATH]. We then try again."
    )

    assert equations.remove_inline_math(text) == expected
    assert equations.remove_inline_math(expected) == expected


def test_inline_with_period_and_whitespace_outside():
    text = r"In the first case, we subtract the thing when $\Delta r<\Delta R.$      We then try again."

    expected = (
        r"In the first case, we subtract the thing when [MATH].      We then try again."
    )

    assert equations.remove_inline_math(text) == expected
    assert equations.remove_inline_math(expected) == expected


def test_both():
    text = r"Given $math$ in equation: $$equation.$$ We aim to find a solution."

    expected = r"Given [MATH] in equation: [EQUATION]. We aim to find a solution."

    assert equations.remove_inline_math(equations.remove_block_math(text)) == expected
    assert (
        equations.remove_inline_math(equations.remove_block_math(expected)) == expected
    )


def test_consecutive():
    text = "[MATH] [MATH] [MATH]"
    expected = "[MATH]"

    assert equations.consecutive_math(text) == expected
    assert equations.consecutive_math(expected) == expected


def test_consecutive_with_multiple_spaces():
    text = "[MATH]    [MATH]  [MATH]"
    expected = "[MATH]"

    assert equations.consecutive_math(text) == expected
    assert equations.consecutive_math(expected) == expected


def test_consecutive_with_newline():
    text = "[MATH] [MATH]\n[MATH]"
    expected = "[MATH]"

    assert equations.consecutive_math(text) == expected
    assert equations.consecutive_math(expected) == expected
