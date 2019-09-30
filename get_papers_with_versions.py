import sqlite3
import re
from typing import Set

from arxiv_util import arxiv_ids

import requests

DB_FILE_NAME = 'arxiv-edits.db'
VERSION_PATTERN = re.compile(r'\[v(.)\]')


def connection():
    return sqlite3.connect(DB_FILE_NAME)


def get_ids_already_queried() -> Set[str]:
    # makes db request
    query = 'SELECT arxiv_id FROM papers WHERE queried = 1'

    con = connection()

    # returns first valiue in tuple
    con.row_factory = lambda cursor, row: row[0]

    ids = con.execute(query).fetchall()

    return set(ids)


def has_multiple_versions(arxiv_id) -> bool:
    # makes network request
    abs_url = f'https://arxiv.org/abs/{arxiv_id}'

    # 1. get the https://arxiv.org/abs/ page
    with requests.get(abs_url) as r:
        r.raise_for_status()
        abs_page = r.text

    # 2. find all the version tags on the page.
    versions = VERSION_PATTERN.findall(abs_page)

    return len(versions) > 1


def add_id(arxiv_id, queried=True, multiple_versions=False):
    # makes db request

    row = (arxiv_id, 1 if queried else 0, 1 if multiple_versions else 0)

    query = 'INSERT INTO papers(arxiv_id, queried, multiple_versions) VALUES (?, ?, ?)'

    con = connection()
    con.execute(query, row)
    con.commit()

    pass


def init_db():
    con = connection()

    with open('schema.sql') as f:
        con.executescript(f.read())


def get_papers_with_versions():
    ids = arxiv_ids()  # generator

    queried_ids: Set[str] = get_ids_already_queried()

    for i in ids:
        if i in queried_ids:
            # print(f'{i} has already been queried.')
            continue

        # write to database
        add_id(i, queried=True,
               multiple_versions=has_multiple_versions(i))


def main():
    # initialize db
    init_db()

    # get papers
    get_papers_with_versions()


main()
