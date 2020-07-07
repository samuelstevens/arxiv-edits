"""
Stores a list of all arxiv ids with multiple versions.
"""
import os
import sqlite3
import datetime
import logging
from typing import (
    Set,
    List,
    Tuple,
    Iterable,
    Dict,
    Callable,
    Iterator,
    cast,
    Generator,
    Collection,
)

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader

from dateutil.parser import parse


from arxivedits import data
from arxivedits.structures import Record, ArxivID, Result, PaperMetadata

URL = "http://export.arxiv.org/oai2"


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


def add_paper(
    arxivid: ArxivID,
    versions: List[int],
    datestamps: List[datetime.datetime],
    authors: List[Tuple[str, str]],
    categories: List[str],
) -> None:
    """
    Stores how many versions a paper has
    """
    con = data.connection()

    try:
        paper_query = "INSERT INTO papers(arxiv_id) VALUES (?)"
        con.execute(paper_query, (arxivid,))
    except sqlite3.IntegrityError:
        print(f"Can't insert {arxivid} into 'papers' table.")

    for first, last in authors:
        try:
            author_query = "INSERT INTO authors VALUES (?, ?, ?)"
            con.execute(author_query, (arxivid, first, last))
        except sqlite3.IntegrityError:
            pass

    for category in categories:
        try:
            category_query = "INSERT INTO categories VALUES (?, ?)"
            con.execute(category_query, (arxivid, category))
        except sqlite3.IntegrityError:
            pass

    for version, date in zip(versions, datestamps):
        try:
            version_query = "INSERT INTO versions VALUES (?, ?, datetime(?))"
            con.execute(
                version_query, (arxivid, version, date.strftime(r"%Y-%m-%d %H:%M:%S"))
            )
        except sqlite3.IntegrityError:
            pass

    con.commit()

    con.close()


def init_db() -> None:
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


def get_all_records() -> Iterator[Tuple[Record, Record]]:
    """
    Creates a generator of all records on arxiv.org.
    """
    arxivraw_reader = MetadataReader(
        fields={
            "versions": ("textList", "arXivRaw:arXivRaw/arXivRaw:version/@version"),
            "dates": (
                "textList",
                "arXivRaw:arXivRaw/arXivRaw:version/arXivRaw:date/text()",
            ),
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

    print("Getting records...")

    records: Generator[Record, None, None] = client.listRecords(metadataPrefix="arXiv")
    records_raw: Generator[Record, None, None] = client.listRecords(
        metadataPrefix="arXivRaw"
    )
    return zip(records, records_raw)


# PARSE


def parse_field(record: Record, field: str) -> Result[List[str]]:
    if not record:
        return ValueError("record cannot be None.")

    _, meta, _ = record

    if not meta:
        return AttributeError("No Metadata found in record.")

    if field not in meta.getMap():
        return AttributeError(f"No {field} found in Metadata.", field)

    return cast(List[str], meta[field])


def parse_timestamp(record: Record) -> Result[List[datetime.datetime]]:
    if not record:
        return ValueError("record cannot be None.")

    _, meta, _ = record

    if not meta:
        return AttributeError("No Metadata found in record.")

    if "dates" not in meta.getMap():
        return AttributeError("No dates found in metadata.")

    datelist = cast(List[str], meta["dates"])

    return [parse(d) for d in datelist]


def parse_authors(record: Record) -> Result[List[Tuple[str, str]]]:
    firstnames = parse_field(record, "firstnames")
    lastnames = parse_field(record, "lastnames")

    if isinstance(firstnames, Exception):
        return firstnames

    if isinstance(lastnames, Exception):
        return lastnames

    try:
        return list(zip(firstnames, lastnames))
    except Exception as err:
        return err


def parse_categories(record: Record) -> Result[List[str]]:
    header, _, _ = record

    try:
        return cast(List[str], header.setSpec())
    except Exception as err:
        return err


def parse_version(record: Record) -> Result[List[int]]:
    version_strs = parse_field(record, "versions")

    if isinstance(version_strs, Exception):
        return version_strs

    versions = [int(v[1:]) for v in version_strs]

    try:
        return versions
    except TypeError:
        return ValueError(f"{versions} is not a List[str].")


def parse_arxivid(record: Record) -> Result[ArxivID]:
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

    logging.info(f"Seen {len(queried_ids)} ids already.")

    for arxiv, raw in get_all_records():
        try:
            arxivid = parse_arxivid(arxiv)
            if isinstance(arxivid, Exception):
                continue

            rawid = parse_arxivid(raw)
            if isinstance(rawid, Exception):
                continue

            versions = parse_version(raw)
            if isinstance(versions, Exception):
                versions = []

            authors = parse_authors(arxiv)
            if isinstance(authors, Exception):
                authors = []

            categories = parse_categories(arxiv)
            if isinstance(categories, Exception):
                categories = []

            datestamps = parse_timestamp(raw)
            if isinstance(datestamps, Exception):
                datestamps = []

            if rawid != arxivid:
                print(f"{rawid} not the same as {arxivid}. Stopping.")
                break

            if arxivid in queried_ids:
                continue

            add_paper(arxivid, versions, datestamps, authors, categories)
        except Exception:
            pass  # do not crash for any reason


def main() -> None:
    """
    Main function
    """
    logging.info("Initializing database.")
    init_db()
    logging.info("Initialized database.")

    logging.info("Getting a record of all documents on arxiv.org")
    get_papers_with_versions()
    logging.info("Recorded all paper's version counts.")


def get_paper_metadata(arxivid: str) -> PaperMetadata:
    with data.connection() as con:
        versions: Dict[int, datetime.datetime] = {}
        categories: Set[str] = set()
        authors: Set[Tuple[str, str]] = set()

        for version_str, date_str, spec, first_name, last_name in con.execute(
            "select versions.number, versions.time, categories.spec, authors.first_name, authors.last_name from versions natural join categories natural join authors where arxiv_id in (?)",
            (arxivid,),
        ).fetchall():
            versions[int(version_str)] = parse(date_str)
            categories.add(spec)
            authors.add((first_name, last_name))

    return PaperMetadata(arxivid, versions, categories, authors)


def get_metadatas(ids: Collection[str]) -> List[PaperMetadata]:
    query_str = "(" + "?, " * (len(ids) - 1) + "?)"

    results: Dict[str, PaperMetadata] = {}

    with data.connection() as con:
        for arxivid, version_str, date_str, spec, first_name, last_name in con.execute(
            "select versions.arxiv_id, versions.number, versions.time, categories.spec, authors.first_name, authors.last_name from versions natural join categories natural join authors where arxiv_id in "
            + query_str,
            ids,
        ).fetchall():
            if arxivid not in results:
                results[arxivid] = PaperMetadata(
                    arxivid,
                    {int(version_str): parse(date_str)},
                    set([spec]),
                    set([(first_name, last_name)]),
                )
            else:
                results[arxivid].versions[int(version_str)] = parse(date_str)
                results[arxivid].categories.add(spec)
                results[arxivid].authors.add((first_name, last_name))

    return list(results.values())


def get_days_delta(paper: PaperMetadata, v1: int, v2: int) -> int:
    difference = paper.versions[v1] - paper.versions[v2]

    return difference.days


def get_avg_time_deltas(
    arxivids: Iterable[str], measure: Callable[[Iterable[int]], float]
) -> Dict[Tuple[int, int], float]:

    version_pairs: Dict[Tuple[int, int], List[int]] = {}

    for arxivid in arxivids:
        paper = get_paper_metadata(arxivid)
        print(paper)

        for v1 in paper.versions:
            v2 = v1 + 1

            days = get_days_delta(paper, v1, v2)

            if (v1, v2) in version_pairs:
                version_pairs[(v1, v2)].append(days)
            else:
                version_pairs[(v1, v2)] = [days]

    return {(v1, v2): measure(version_pairs[(v1, v2)]) for v1, v2 in version_pairs}


if __name__ == "__main__":
    main()
