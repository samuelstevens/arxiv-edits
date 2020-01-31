"""
Provides a central location to store all data locations
"""

import sqlite3
import os
import pathlib

from typing import Tuple, List
from arxivedits.structures import Res

pwd = pathlib.Path(__file__).parent.parent.absolute()  # pylint: disable=invalid-name
DATA_DIR = pwd / "data"  # arxivedits/data, NOT arxivedits/arxivedits/data

SCHEMA_PATH = pwd / "schema.sql"


def path_asserts(arxividpath: str, version: int):
    """
    Asserts that paths and folders are correctly formed.
    """
    assert "\\" not in arxividpath and "/" not in arxividpath
    path = os.path.join(DATA_DIR, arxividpath, f"v{version}", "extra")
    os.makedirs(path, exist_ok=True)


def parse_filename(filename: str) -> Res[Tuple[str, int]]:
    """
    Parses a filename into `arxividpath` and `version`
    """
    _, filename = os.path.split(filename)

    arxivid = filename[:-3]
    try:
        version = int(filename[-1])
    except ValueError:
        return ValueError(f"{filename} not a valid arxivid")

    arxividpath = arxivid.replace("/", "-")

    return arxividpath, version


def extrafiles_path(arxividpath: str, version: int) -> str:
    path_asserts(arxividpath, version)

    return os.path.join(DATA_DIR, arxividpath, f"v{version}", "extra")


def source_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the .gz file for a given arxivid and version.
    """
    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR, arxividpath, f"v{version}", "extra", f"{arxividpath}-v{version}.gz"
    )


def text_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the detexed file for a given arxivid and version.
    """

    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR, arxividpath, f"v{version}", "extra", f"{arxividpath}-v{version}.txt"
    )


def sentence_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the sentence-split file for a given arxivid and version.
    """

    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR, arxividpath, f"v{version}", f"{arxividpath}-v{version}-sentences.txt"
    )


def latex_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the constructed .tex file for a given arxivid and version.
    """

    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR,
        arxividpath,
        f"v{version}",
        "extra",
        f"{arxividpath}-v{version}-original.tex",
    )


def clean_latex_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the cleaned .tex file for a given arxivid and version.
    """

    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR,
        arxividpath,
        f"v{version}",
        "extra",
        f"{arxividpath}-v{version}-clean.tex",
    )


def pdf_path(arxividpath: str, version: int) -> str:
    """
    Returns the path for the original pdf file for a given arxivid and version.
    """

    path_asserts(arxividpath, version)

    return os.path.join(
        DATA_DIR, arxividpath, f"v{version}", f"{arxividpath}-v{version}.pdf",
    )


def get_local_files(maximum_only: bool = False) -> List[Tuple[str, int]]:
    idlist = []

    for arxivid in os.listdir(DATA_DIR):
        versionlist = []

        if not os.path.isdir(os.path.join(DATA_DIR, arxivid)):
            continue

        for v in os.listdir(os.path.join(DATA_DIR, arxivid)):
            try:
                version = int(v[1:])
                versionlist.append(version)
            except ValueError:
                continue

        if maximum_only and versionlist:
            versionlist = [max(versionlist)]

        idlist.extend([(arxivid, v) for v in versionlist])

    return sorted(idlist)


SECTIONS_DIR = os.path.join(DATA_DIR, "sections")
UNZIPPED_DIR = os.path.join(DATA_DIR, "unzipped")
ALIGNMENTS_DIR = os.path.join(DATA_DIR, "alignments")

DB_FILE_NAME = os.path.join(DATA_DIR, "arxivedits.sqlite3")
IDF_DB = os.path.join(DATA_DIR, "idf")

# if not os.path.isdir(DATA_DIR):
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SECTIONS_DIR, exist_ok=True)
os.makedirs(UNZIPPED_DIR, exist_ok=True)
os.makedirs(ALIGNMENTS_DIR, exist_ok=True)


def connection():
    """
    Creates and returns a new connection to a persistent database
    """
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)


def is_x(arxivid, versioncount, directory, extension="") -> bool:
    """
    Checks if all versions of an arxiv id are in a directory. Useful to see what % were successfully 'detexed' or extracted.
    """
    arxividpath = arxivid.replace("/", "-")

    for i in range(versioncount):
        filepath = os.path.join(directory, f"{arxividpath}-v{i + 1}{extension}")
        if not os.path.isfile(filepath):
            return False

    return True
