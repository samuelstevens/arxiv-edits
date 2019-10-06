import pytest

from arxivedits.versions import parse
from oaipmh.common import Header, Metadata


def test_parse_empty():
    record = None
    assert parse(record) == ('', False)


def test_parse_empty_tuple():
    record = ()
    assert parse(record) == ('', False)


def test_parse_empty_values():
    record = (None, None, None)
    assert parse(record) == ('', False)


def test_parse_no_map():
    m = Metadata('element', {})
    record = (None, m, None)
    assert parse(record) == ('', False)


def test_parse_no_id():
    m = Metadata('element', {'versions': []})
    record = (None, m, None)
    assert parse(record) == ('', False)


def test_parse_empty_id():
    m = Metadata('element', {'versions': [], 'id': []})
    record = (None, m, None)
    assert parse(record) == ('', False)


def test_parse_no_versions():
    i = '0704.0001'
    m = Metadata('element', {'versions': [], 'id': [i]})
    record = (None, m, None)
    assert parse(record) == (i, False)


def test_parse_one_version():
    i = '0704.0001'
    m = Metadata('element', {'versions': ['v1'], 'id': [i]})
    record = (None, m, None)
    assert parse(record) == (i, False)


def test_parse_two_versions():
    i = '0704.0001'
    m = Metadata('element', {'versions': ['v1', 'v2'], 'id': [i]})
    record = (None, m, None)
    assert parse(record) == (i, True)


def test_parse_three_versions():
    i = '0704.0001'
    m = Metadata('element', {'versions': ['v1', 'v2', 'v3'], 'id': [i]})
    record = (None, m, None)
    assert parse(record) == (i, True)


def test_parse_three_versions_no_id():
    m = Metadata('element', {'versions': ['v1', 'v2', 'v3'], 'id': []})
    record = (None, m, None)
    assert parse(record) == ('', False)
