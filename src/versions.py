# built in
from typing import Set, List, Tuple, NewType

# external
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader

# internal
from db import connection
from types import Record, ArxivID

URL = 'http://export.arxiv.org/oai2'
METADATA_PREFIX = 'arXivRaw'


def write_error(record: Record):
    '''
    Writes the record to a file to show an error. Doesn't work, because `record` is a ref.
    '''
    with open('errors.txt', 'a') as file:
        file.write(str(record))


def get_ids_already_queried() -> Set[ArxivID]:
    '''
    Finds all `ArxivID` that exist in the database.
    '''
    # makes db request
    query = 'SELECT arxiv_id FROM papers'

    con = connection()

    # returns first valiue in tuple
    con.row_factory = lambda cursor, row: row[0]

    ids = con.execute(query).fetchall()

    return set(ids)


def add_id(arxiv_id: ArxivID, multiple_versions: bool):
    '''
    Stores whether a paper has multiple versions.
    '''

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

    with open('schema.sql') as file:
        con.executescript(file.read())


def get_records():
    '''
    Creates a generator of all records on arxiv.org.
    '''
    arxivraw_reader = MetadataReader(
        fields={
            'versions': ('textList', 'arXivRaw:arXivRaw/arXivRaw:version/@version'),
            'id': ('textList', 'arXivRaw:arXivRaw/arXivRaw:id/text()'),
        },
        namespaces={
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'arXivRaw': 'http://arxiv.org/OAI/arXivRaw/'}
    )

    registry = MetadataRegistry()
    registry.registerReader(METADATA_PREFIX, arxivraw_reader)

    client = Client(URL, registry, force_http_get=True, custom_retry_policy={
        # retry on both 500 and 503 HTTP return codes
        'expected-errcodes': {500, 503},
        # wait for 30 seconds before retrying
        'wait-default': 60,
        # retry 10 times
        'retry': 10,
    })

    client.updateGranularity()

    records = client.listRecords(metadataPrefix=METADATA_PREFIX)

    return records


def parse(record: Record) -> Tuple[str, bool]:
    '''
    Takes a Record and returns the identifier and whether it has multiple versions
    '''

    invalid = ('', False)

    if not record:
        return invalid

    _, meta, _ = record

    if not meta:
        return invalid

    # assuming that it won't come out as just a string.
    id_list: List[str] = meta['id']

    if not id_list:
        return invalid

    try:
        i = id_list[0]
        if len(i) < 9:  # not a valid arxiv ID.
            print(f'{i} is not a valid arxiv ID.')
            return invalid
    except TypeError:
        print(f'{i} is not a List[str].')
        return invalid

    # can now assume i is a valid arxiv ID.

    versions: List[str] = meta['versions']

    multiple_versions = False

    try:
        multiple_versions = len(versions) > 1
    except TypeError:
        print(f'{versions} is not a List[str].')

    return (i, multiple_versions)


def get_papers_with_versions():
    '''
    Scrapes arxiv.org for all papers with multiple versions.
    '''

    queried_ids: Set[str] = get_ids_already_queried()

    records = get_records()

    for record in records:
        i, multiple_versions = parse(record)

        if not i:
            # print('Missing id.')
            continue

        if i in queried_ids:
            # print(f'{i} has already been queried.')
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


if __name__ == '__main__':
    main()
