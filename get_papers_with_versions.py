# built in
import sqlite3
from typing import Set

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader


URL = 'http://export.arxiv.org/oai2'
METADATA_PREFIX = 'arXivRaw'


DB_FILE_NAME = 'arxiv-edits.db'


def connection():
    return sqlite3.connect(DB_FILE_NAME)


def get_ids_already_queried() -> Set[str]:
    # makes db request
    query = 'SELECT arxiv_id FROM papers'

    con = connection()

    # returns first valiue in tuple
    con.row_factory = lambda cursor, row: row[0]

    ids = con.execute(query).fetchall()

    return set(ids)


def add_id(arxiv_id, multiple_versions):
    # makes db request

    row = (arxiv_id, 1 if multiple_versions else 0)

    query = 'INSERT INTO papers(arxiv_id, multiple_versions) VALUES (?, ?)'

    con = connection()
    con.execute(query, row)
    con.commit()


def init_db():
    '''
    Initializes the database using ./schema.sql
    '''

    con = connection()

    with open('schema.sql') as f:
        con.executescript(f.read())


def get_records():
    arXivRaw_reader = MetadataReader(
        fields={
            'versions': ('textList', 'arXivRaw:arXivRaw/arXivRaw:version/@version'),
            'id': ('textList', 'arXivRaw:arXivRaw/arXivRaw:id/text()')
        },
        namespaces={
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'arXivRaw': 'http://arxiv.org/OAI/arXivRaw/'}
    )

    registry = MetadataRegistry()
    registry.registerReader(METADATA_PREFIX, arXivRaw_reader)

    client = Client(URL, registry)

    records = client.listRecords(metadataPrefix=METADATA_PREFIX)

    return records


def get_papers_with_versions():
    '''
    Scrapes arxiv.org for all papers with multiple versions.
    '''

    queried_ids: Set[str] = get_ids_already_queried()

    records = get_records()

    for record in records:
        i = record[1]['id'][0]
        multiple_versions = len(record[1]['versions']) > 1

        if i in queried_ids:
            print(f'{i} has already been queried.')
            continue

        add_id(i, multiple_versions)


def main():
    '''
    Main function
    '''

    # initialize db
    init_db()

    # get papers
    get_papers_with_versions()


main()
