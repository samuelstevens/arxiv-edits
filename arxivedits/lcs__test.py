from hypothesis import given, example
from hypothesis import strategies as st
from lcs import lcs


@given(st.lists(st.text()))
@example([])
def test_lcs_with_duplicate(s):
    assert lcs(s, s) == s


@given(st.lists(st.text()))
@example([])
def test_lcs_with_empty(s):
    assert lcs(s, []) == []


@given(st.lists(st.text()))
@example([])
def test_lcs_with_double(s):
    assert lcs(s, s + s) == s


test_lcs_with_duplicate()
test_lcs_with_empty()
test_lcs_with_double()
