from arxivedits import diff


def test_sent_filter_math():
    sentence = "[MATH], [MATH] and more [MATH]."
    assert not diff.sent_filter(sentence)


def test_sent_filter_math_pass():
    sentence = "[MATH], [EQUATION] and more [MATH] consistently demonstrate that we have enough words to pass this test."
    assert diff.sent_filter(sentence)


def test_sent_filter_title():
    sentence = "## Section Title"
    assert diff.sent_filter(sentence)
