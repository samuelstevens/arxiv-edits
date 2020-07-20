from arxivedits import source


def test_easy_eps():
    mime = "application/postscript"
    raw = "PostScript document text conforming DSC level 2.0, type EPS"

    expected_filetype = source.FileType.POSTSCRIPT

    assert source.parse_filetype(mime, raw) == expected_filetype


def test_easy_tar():
    mime = "application/x-tar"
    raw = "POSIX tar archive (GNU)"

    expected_filetype = source.FileType.TAR

    assert source.parse_filetype(mime, raw) == expected_filetype


def test_easy_gzip():
    mime = "application/gzip"
    raw = 'gzip compressed data, was "0704.0001.tar", last modified: Tue Jul 24 20:10:27 2007, max compression, from Unix'

    expected_filetype = source.FileType.GZIP

    assert source.parse_filetype(mime, raw) == expected_filetype


def test_different_gzip_mime():
    mime = "application/octet-stream"
    raw = "gzip compressed data, last modified: Fri Jan  6 01:05:46 2017, from Unix gz"

    expected_filetype = source.FileType.GZIP

    assert source.parse_filetype(mime, raw) == expected_filetype


def test_easy_tex():
    mime = "text/x-tex"
    raw = "LaTeX 2e document, ASCII text"

    expected_filetype = source.FileType.TEX

    assert source.parse_filetype(mime, raw) == expected_filetype

