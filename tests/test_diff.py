from hypothesis import given
import hypothesis.strategies as st

from arxivedits import diff, filters


def test_sent_filter_math():
    sentence = "[MATH], [MATH] and more [MATH]."
    assert not filters.sent_filter(sentence)


def test_sent_filter_math_pass():
    sentence = "[MATH], [EQUATION] and more [MATH] consistently demonstrate that we have enough words to pass this test."
    assert filters.sent_filter(sentence)


def test_sent_filter_title():
    sentence = "## Section Title"
    assert filters.sent_filter(sentence)


@given(
    st.lists(st.text(st.characters(min_codepoint=1))),
    st.lists(st.text(st.characters(min_codepoint=1))),
)
def test_lcs(a, b):
    result = diff.fast_diff(a * 4, b * 4)
    assert len(result) >= len(a * 4)
    assert len(result) >= len(b * 4)
