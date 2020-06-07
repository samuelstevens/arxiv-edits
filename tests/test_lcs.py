from hypothesis import given
import hypothesis.strategies as st

from arxivedits import lcs


@given(st.lists(st.text()))
def test_lcs_with_empty(a):
    result = lcs.lcs(a, [])
    assert result == []


@given(
    st.lists(st.text(st.characters(min_codepoint=1))),
    st.lists(st.text(st.characters(min_codepoint=1))),
)
def test_lcs(a, b):
    result = lcs.lcs(a, b)
    assert len(result) <= len(a)
    assert len(result) <= len(b)
