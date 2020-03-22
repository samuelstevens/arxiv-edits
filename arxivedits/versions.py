"""
Stores a list of all arxiv ids with multiple versions.
"""
import os
import sqlite3
from typing import Set, List, Tuple, Iterable

from oaipmh.client import Client  # type: ignore
from oaipmh.metadata import MetadataRegistry, MetadataReader  # type: ignore


from arxivedits import data
from arxivedits.structures import Record, ArxivID, Res

URL = "http://export.arxiv.org/oai2"
METADATA_PREFIX = "arXivRaw"


def get_ids_already_queried() -> Set[ArxivID]:
    """
    Finds all `ArxivID` that exist in the database.
    """
    # makes db request
    query = "SELECT arxiv_id FROM papers"

    con = data.connection()

    # returns first valiue in tuple
    con.row_factory = lambda cursor, row: row[0]

    ids = con.execute(query).fetchall()

    return set(ids)


def add_record(
    arxivid: ArxivID, versioncount: int, authors: List[str], categories: List[str]
):
    """
    Stores how many versions a paper has
    """
    con = data.connection()

    try:
        paper_query = "INSERT INTO papers(arxiv_id, version_count) VALUES (?, ?)"
        con.execute(paper_query, (arxivid, versioncount))
    except sqlite3.IntegrityError:
        pass

    for author in authors:
        try:
            author_query = "INSERT INTO authors VALUES (?)"
            con.execute(author_query, (author,))
        except sqlite3.IntegrityError:
            pass

    for category in categories:
        try:
            category_query = "INSERT INTO categories VALUES (?)"
            con.execute(category_query, (category,))
        except sqlite3.IntegrityError:
            pass

        try:
            category_query = "INSERT INTO categories VALUES (?)"
            con.execute(category_query, (category,))
        except sqlite3.IntegrityError:
            pass

    con.commit()

    con.close()


def init_db():
    """
    Initializes the database using ./schema.sql
    """

    con = data.connection()

    if not os.path.isfile(data.SCHEMA_PATH):
        raise AttributeError(
            f"No schema.sql found. Please move it to {data.SCHEMA_PATH} or edit arxivedits/data.py's SCHEMA_PATH variable."
        )

    with open(data.SCHEMA_PATH) as file:
        con.executescript(file.read())


def get_all_records() -> Iterable[Tuple[Record, Record]]:
    """
    Creates a generator of all records on arxiv.org.
    """
    arxivraw_reader = MetadataReader(
        fields={
            "versions": ("textList", "arXivRaw:arXivRaw/arXivRaw:version/@version"),
            "id": (
                "textList",
                "arXivRaw:arXivRaw/arXivRaw:id/text()",
            ),  # always an array, even if type is "text"
        },
        namespaces={
            "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "arXivRaw": "http://arxiv.org/OAI/arXivRaw/",
        },
    )

    arxiv_reader = MetadataReader(
        fields={
            "lastnames": (
                "textList",
                "arXiv:arXiv/arXiv:authors/arXiv:author/arXiv:keyname/text()",
            ),
            "firstnames": (
                "textList",
                "arXiv:arXiv/arXiv:authors/arXiv:author/arXiv:forenames/text()",
            ),  # we assume forenames and keynames arrive in the same order.
            "id": (
                "textList",
                "arXiv:arXiv/arXiv:id/text()",
            ),  # always an array, even if type is "text"
            "categories": (
                "textList",
                "arXiv:arXiv/arXiv:categories/text()",
            ),  # always an array, even if type is "text"
        },
        namespaces={
            "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "arXiv": "http://arxiv.org/OAI/arXiv/",
        },
    )

    registry = MetadataRegistry()
    registry.registerReader("arXiv", arxiv_reader)
    registry.registerReader("arXivRaw", arxivraw_reader)

    client = Client(
        URL,
        registry,
        force_http_get=True,
        custom_retry_policy={
            # retry on both 500 and 503 HTTP return codes
            "expected-errcodes": {500, 503},
            # wait for 30 seconds before retrying
            "wait-default": 30,
            # retry 10 times
            "retry": 10,
        },
    )

    client.updateGranularity()

    records = client.listRecords(metadataPrefix="arXiv")
    records_raw = client.listRecords(metadataPrefix="arXivRaw")
    return zip(records, records_raw)  # assumes that


def parse_field(record: Record, field: str) -> Res[List[str]]:
    if not record:
        return ValueError("record cannot be None.")

    _, meta, _ = record

    if not meta:
        return AttributeError("No Metadata found in record.")

    if field not in meta.getMap():
        return AttributeError("No ID found in Metadata.")

    print(meta.getField(field))

    return meta[field]


def parse_authors(record: Record) -> Res[List[str]]:
    firstnames = parse_field(record, "firstnames")
    lastnames = parse_field(record, "lastnames")

    if isinstance(firstnames, Exception):
        return firstnames

    if isinstance(lastnames, Exception):
        return lastnames

    try:
        return [first + last for first, last in zip(firstnames, lastnames)]
    except TypeError as err:
        return err


def parse_categories(record: Record) -> Res[List[str]]:
    category_list = parse_field(record, "categories")

    if isinstance(category_list, Exception):
        return category_list

    try:
        category_string = category_list[0]
        return category_string.split()
    except TypeError:
        return ValueError(f"{category_list} is not List[str].")


def parse_version(record: Record) -> Res[int]:
    versions = parse_field(record, "versions")

    if isinstance(versions, Exception):
        return versions

    try:
        return len(versions)
    except TypeError:
        return ValueError(f"{versions} is not a List[str].")


def parse_arxivid(record: Record) -> Res[ArxivID]:
    id_list = parse_field(record, "id")

    if isinstance(id_list, Exception):
        return id_list

    try:
        return ArxivID(id_list[0])
    except TypeError:
        return ValueError(f"{id_list} is not List[str].")


def get_papers_with_versions() -> None:
    """
    Scrapes arxiv.org for all papers with multiple versions.
    """

    queried_ids = get_ids_already_queried()

    for arxiv, raw in get_all_records():

        arxivid = parse_arxivid(arxiv)

        if isinstance(arxivid, Exception):
            continue

        rawid = parse_arxivid(raw)

        if isinstance(rawid, Exception):
            continue

        versions = parse_version(raw)

        if isinstance(versions, Exception):
            versions = -1

        authors = parse_authors(arxiv)

        if isinstance(authors, Exception):
            authors = []

        categories = parse_categories(arxiv)
        if isinstance(categories, Exception):
            categories = []

        print(arxivid, rawid, versions, authors, categories)

        if rawid != arxivid:
            print(f"{rawid} not the same as {arxivid}. Stopping.")
            break

        if arxivid in queried_ids:
            continue

        add_record(arxivid, versions, authors, categories)


def main() -> None:
    """
    Main function
    """

    init_db()
    print("Initialized database succesfully.")

    get_papers_with_versions()
    print("Recorded all paper's version counts.")


if __name__ == "__main__":
    # get_categories_and_authors()
    # main()
    # add_record("0704.0001", 3, ["author 3", "author 4"], ["hep-ph"])
    pass
