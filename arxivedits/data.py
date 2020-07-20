"""
Provides a central location to store all data locations
"""

import sqlite3
import os
import pathlib
import csv

from typing import Tuple, List, Union, Iterator
from arxivedits.structures import Result, ArxivID, ArxivIDPath

# TYPES

UnsafeArxivID = Union[ArxivID, ArxivIDPath, str]

# PATHS

pwd = pathlib.Path(__file__).parent.parent.absolute()
DATA_DIR = pwd / "data"
ALIGNMENT_DIR = DATA_DIR / "alignments"
MODEL_DIR = ALIGNMENT_DIR / "models"
CSV_DIR = ALIGNMENT_DIR / "alignments"
MACHINE_DIR = ALIGNMENT_DIR / "machine-annotations"
ANNOTATION_DIR = ALIGNMENT_DIR / "need-annotation"
FINISHED_DIR = ALIGNMENT_DIR / "finished-annotations"
VISUAL_DIR = DATA_DIR / "visualizations"
SCHEMA_PATH = pwd / "schema.sql"
DB_FILE_NAME = os.path.join(DATA_DIR, "arxivedits.sqlite3")

DOWNLOAD_DIR = pwd / "arxiv-downloads"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(ALIGNMENT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(ANNOTATION_DIR, exist_ok=True)
os.makedirs(FINISHED_DIR, exist_ok=True)
os.makedirs(VISUAL_DIR, exist_ok=True)


# TYPE FUNCTIONS


def id_to_path(arxivid: UnsafeArxivID) -> ArxivIDPath:
    """
    Replaces the / from an id with a -
    - also used for type conversion to satistfy mypy.
    """
    return ArxivIDPath(arxivid.replace("/", "-"))


def alignment_path_asserts(
    arxivid: UnsafeArxivID, version1: int, version2: int
) -> ArxivIDPath:
    """
    Asserts that paths and folders are correctly formed for alignment.
    """
    arxividpath = id_to_path(arxivid)

    assert version1 < version2, f"v{version1} must be less than v{version2}"

    return arxividpath


# PATH FUNCTIONS


def parse_filename(filename: str) -> Result[Tuple[str, int]]:
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


def extrafiles_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    The folder for all extra files for an arxivid and version 
    """
    arxividpath = id_to_path(arxivid)

    return os.path.join(DOWNLOAD_DIR, arxividpath, f"v{version}", "extra")


def source_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    Returns the path for the .gz file for a given arxivid and version 
    """

    arxividpath = id_to_path(arxivid)

    return os.path.join(
        DOWNLOAD_DIR,
        arxividpath,
        f"v{version}",
        "extra",
        f"{arxividpath}-v{version}.gz",
    )


def text_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    Returns the path for the detexed file for a given arxivid and version
    """

    arxividpath = id_to_path(arxivid)

    return os.path.join(
        DOWNLOAD_DIR,
        arxividpath,
        f"v{version}",
        "extra",
        f"{arxividpath}-v{version}.txt",
    )


def sentence_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    Returns the path for the sentence-split file for a given arxivid
    """

    arxividpath = id_to_path(arxivid)

    return os.path.join(
        DOWNLOAD_DIR,
        arxividpath,
        f"v{version}",
        f"{arxividpath}-v{version}-sentences.txt",
    )


def latex_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    Returns the path for the constructed .tex file for a given arxivid and version 
    """

    arxividpath = id_to_path(arxivid)

    return os.path.join(
        DOWNLOAD_DIR,
        arxividpath,
        f"v{version}",
        "extra",
        f"{arxividpath}-v{version}-original.tex",
    )


def pdf_path(arxivid: UnsafeArxivID, version: int) -> str:
    """
    Returns the path for the original pdf file for a given arxivid and version and whether it exists.
    """

    arxividpath = id_to_path(arxivid)

    return os.path.join(
        DOWNLOAD_DIR, arxividpath, f"v{version}", f"{arxividpath}-v{version}.pdf",
    )


def alignment_model_path(
    arxivid: UnsafeArxivID, version1: int, version2: int, unaligned_sentences: int
) -> str:
    """
    Returns the path for the Alignment() .pckl file for a given version pair.
    """

    arxividpath = alignment_path_asserts(arxivid, version1, version2)

    return os.path.join(
        MODEL_DIR,
        f"{arxividpath}-v{version1}-v{version2}-({unaligned_sentences}-unaligned-sents).pckl",
    )


def alignment_csv_path(arxivid: UnsafeArxivID, version1: int, version2: int) -> str:
    """
    Returns the path for the alignment .csv file for a given version pair.
    """

    arxividpath = alignment_path_asserts(arxivid, version1, version2)

    return os.path.join(CSV_DIR, f"{arxividpath}-v{version1}-v{version2}.csv")


def machine_csv_path(arxivid: UnsafeArxivID, version1: int, version2: int) -> str:
    """
    Returns the path for the machine aligned-pairs.
    """

    arxividpath = alignment_path_asserts(arxivid, version1, version2)

    return os.path.join(MACHINE_DIR, f"{arxividpath}-v{version1}-v{version2}.csv")


def alignment_annotation_path(
    arxivid: UnsafeArxivID, version1: int, version2: int, unaligned_sentences: int
) -> str:
    """
    Returns the path for the manual annotation .csv file for a given version pair.
    """

    arxividpath = alignment_path_asserts(arxivid, version1, version2)

    return os.path.join(
        ANNOTATION_DIR,
        f"{arxividpath}-v{version1}-v{version2}-({unaligned_sentences}-unaligned-sents).csv",
    )


def alignment_finished_path(
    arxivid: UnsafeArxivID, version1: int, version2: int, unaligned_sentences: int
) -> str:
    """
    Returns the path for the finisehd annotation .csv file for a given version pair.
    """

    arxividpath = alignment_path_asserts(arxivid, version1, version2)

    return os.path.join(
        FINISHED_DIR,
        f"{arxividpath}-v{version1}-v{version2}-({unaligned_sentences}-unaligned-sents).csv",
    )


def get_local_files(maximum_only: bool = False) -> List[Tuple[ArxivIDPath, int]]:
    idlist: List[Tuple[ArxivIDPath, int]] = []

    for arxivid in os.listdir(DOWNLOAD_DIR):
        versionlist = []

        if not os.path.isdir(os.path.join(DOWNLOAD_DIR, arxivid)):
            continue

        for v in os.listdir(os.path.join(DOWNLOAD_DIR, arxivid)):
            try:
                version = int(v[1:])
                versionlist.append(version)
            except ValueError:
                continue

        if maximum_only and versionlist:
            versionlist = [max(versionlist)]

        idlist.extend([(ArxivIDPath(arxivid), v) for v in versionlist])

    return sorted(idlist)


def get_sample_files(maximum_only: bool = False) -> List[Tuple[ArxivID, int]]:
    with open(os.path.join(DATA_DIR, "sample-only-multiversion.csv")) as csvfile:
        reader = csv.reader(csvfile)
        pairs = [(i, int(versioncount)) for i, versioncount in reader]

    idlist = []

    for arxivid, versioncount in pairs:
        versionlist = list(range(1, versioncount + 1))

        arxvidpath = id_to_path(ArxivID(arxivid))

        if not os.path.isdir(os.path.join(DOWNLOAD_DIR, arxvidpath)):
            continue

        if maximum_only and versionlist:
            versionlist = [max(versionlist)]

        idlist.extend([(ArxivID(arxivid), v) for v in versionlist])

    return idlist


def get_all_files(maximum_only: bool = False) -> Iterator[Tuple[ArxivID, int]]:
    """
    Gets all arxivid, version_count pairs in the .sqlite3 database where version_count > 1 (at least two versions of a paper).
    """

    # return [("1105.6010", 1)]

    # return [
    #     ("1612.00043", 1),
    #     ("1602.08739", 2),
    #     ("1701.08393", 1),
    #     ("1701.08393", 2),
    #     ("1701.08393", 2),
    #     ("1701.08393", 3),
    #     ("1504.02209", 2),
    #     ("1511.00980", 1),
    #     ("hep-lat-0001001", 1),
    #     ("hep-lat-0001001", 2),
    #     ("1409.3945", 4),
    #     ("1409.3945", 4),
    #     ("1710.04570", 1),
    #     ("1710.04570", 2),
    #     ("1710.04570", 2),
    #     ("1710.04570", 3),
    #     ("1710.04570", 3),
    #     ("1710.04570", 4),
    #     ("1710.04570", 4),
    #     ("1710.04570", 5),
    #     ("1506.05557", 2),
    #     ("1307.2982", 2),
    #     ("1307.2982", 2),
    #     ("1307.2982", 3),
    #     ("1408.0382", 2),
    #     ("1408.0382", 2),
    #     ("1204.2729", 3),
    #     ("1506.03158", 1),
    #     ("1209.4282", 1),
    #     ("cond-mat-9609177", 1),
    #     ("1904.03047", 1),
    #     ("1904.03047", 2),
    #     ("1802.00450", 1),
    #     ("1802.00450", 2),
    #     ("1704.00339", 1),
    #     ("1704.00339", 2),
    #     ("1511.04932", 2),
    #     ("1802.08924", 1),
    #     ("1212.6548", 2),
    #     ("1212.6548", 2),
    #     ("1710.09926", 2),
    #     ("math-ph-0208014", 2),
    #     ("1803.05212", 1),
    #     ("1105.6010", 1),
    #     ("1105.6010", 2),
    #     ("hep-th-0302160", 1),
    #     ("hep-th-0302160", 2),
    #     ("1503.05281", 1),
    #     ("1503.05281", 2),
    #     ("1901.03420", 1),
    #     ("1901.03420", 2),
    #     ("1901.03420", 2),
    #     ("1901.03420", 3),
    #     ("1901.03420", 3),
    #     ("1901.03420", 4),
    #     ("1711.00038", 2),
    #     ("1711.00038", 2),
    #     ("1412.5031", 1),
    #     ("1412.5031", 2),
    #     ("0709.3810", 1),
    #     ("1910.07486", 1),
    #     ("1910.07486", 2),
    #     ("math-0510123", 2),
    #     ("1703.09021", 2),
    #     ("1703.09021", 3),
    #     ("1811.03215", 4),
    #     ("1811.03215", 4),
    #     ("hep-ph-0310033", 2),
    #     ("1906.10109", 1),
    #     ("1906.10109", 2),
    #     ("1410.2177", 3),
    #     ("0710.5616", 1),
    #     ("0710.5616", 2),
    #     ("gr-qc-0207074", 2),
    #     ("gr-qc-0207074", 2),
    #     ("0911.0713", 2),
    #     ("1902.11123", 4),
    #     ("1902.11123", 4),
    #     ("1902.11123", 5),
    #     ("1801.06856", 3),
    # ]

    # return [("1602.08739", 2)] + [(s[0], s[1]) for s in SAMPLE_IDS]

    return get_sample_files(maximum_only=maximum_only)

    def result_iter(cursor: sqlite3.Cursor) -> Iterator[Tuple[ArxivID, int]]:
        """
        https://code.activestate.com/recipes/137270-use-generators-for-fetching-large-db-record-sets/
        """

        while True:
            results = cursor.fetchmany()
            if not results:
                break
            for arxivid, version_str in results:
                versions = int(version_str)

                if maximum_only:
                    yield arxivid, versions
                else:
                    for version in range(1, versions + 1):
                        yield arxivid, version

    query = "SELECT arxiv_id, MAX(number) FROM versions GROUP BY arxiv_id HAVING MAX(number) > 1;"

    return result_iter(connection().execute(query))


def get_all_pairs() -> Iterator[Tuple[ArxivID, int, int]]:
    for arxivid, versions in get_all_files(maximum_only=True):
        for v1 in range(1, versions):
            yield arxivid, v1, v1 + 1


def get_paragraphs(arxivid: UnsafeArxivID, version: int) -> Result[List[List[str]]]:
    """
    Gets a list of lists of sentences representing document paragraphs.
    """
    arxividpath = id_to_path(arxivid)

    try:
        with open(sentence_path(arxividpath, version)) as file:
            contents = file.read()
    except FileNotFoundError as err:
        return err

    paragraph_texts = contents.split("\n\n")

    paragraphs = [
        [sent for sent in paragraph.split("\n") if sent]
        for paragraph in paragraph_texts
    ]

    paragraphs = [p for p in paragraphs if p]

    return paragraphs


def compare_command(arxivid: UnsafeArxivID, v1: int, v2: int) -> str:
    arxividpath = id_to_path(arxivid)

    sent_path_v1 = sentence_path(arxividpath, v1)
    sent_path_v2 = sentence_path(arxividpath, v2)

    return f"code --diff {sent_path_v1} {sent_path_v2}"


def connection() -> sqlite3.Connection:
    """
    Creates and returns a new connection to a persistent database
    """
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)


def is_x(
    arxivid: UnsafeArxivID, versioncount: int, directory: str, extension: str = ""
) -> bool:
    """
    Checks if all versions of an arxiv id are in a directory. Useful to see what % were successfully 'detexed' or extracted.
    """
    arxividpath = arxivid.replace("/", "-")

    for i in range(versioncount):
        filepath = os.path.join(directory, f"{arxividpath}-v{i + 1}{extension}")
        if not os.path.isfile(filepath):
            return False

    return True


def is_detexed(arxivid: UnsafeArxivID, version: int) -> bool:
    return os.path.isfile(text_path(arxivid, version))


SAMPLE_IDS = [
    ("1906.06209", 1, 2),
    ("1004.1666", 1, 2),
    ("1902.05725", 1, 2),
    ("1409.3945", 2, 3),
    ("1410.4028", 1, 2),
    ("math-0104116", 1, 2),
    ("1602.08631", 3, 4),
    ("1306.1389", 1, 2),
    ("1512.05089", 1, 2),
    ("1610.01333", 1, 2),
    ("1305.6088", 1, 2),
    ("1406.2192", 1, 2),
    ("1102.5645", 1, 2),
    ("cond-mat-0602186", 4, 5),
    ("1412.6539", 2, 3),
    ("1204.5014", 1, 2),
    ("0803.2581", 1, 2),
    ("1806.05893", 1, 2),
    ("1811.07450", 1, 2),
    ("hep-th-0607021", 1, 2),
]

ANNOTATED_IDS = [
    ("1906.06209", 1, 2),
    ("1004.1666", 1, 2),
    ("1902.05725", 1, 2),
    ("1409.3945", 2, 3),
    ("1410.4028", 1, 2),
    ("math-0104116", 1, 2),
    ("1306.1389", 1, 2),
    ("1512.05089", 1, 2),
    ("1610.01333", 1, 2),
    ("1305.6088", 1, 2),
    ("1406.2192", 1, 2),
    ("1102.5645", 1, 2),
    ("cond-mat-0602186", 4, 5),
    ("1412.6539", 2, 3),
    ("1204.5014", 1, 2),
    ("0803.2581", 1, 2),
    ("1806.05893", 1, 2),
    ("1811.07450", 1, 2),
]
