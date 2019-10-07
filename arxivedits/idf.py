from typing import List, Set
import shelve

from db import connection
from structures import ArxivID
from tex import detex, download_tex_src
from nlp import ArxivTokenizer

import requests

t = ArxivTokenizer()

IDF_DB = 'data/idf'
TEX_DB = 'data/tex'


def ids() -> List[ArxivID]:
    '''
    Returns a pseudo-list of arxivIDs with multiple versions.
    '''
    query = 'SELECT arxiv_id FROM papers WHERE multiple_versions = 1'
    con = connection()
    con.row_factory = lambda cursor, row: row[0]
    ids = con.execute(query)

    return ids


def get_src(arxiv_id: ArxivID) -> List[str]:
    srcs = []

    try:
        srcs = download_tex_src(arxiv_id, clean=False)
    except requests.exceptions.HTTPError as e:
        print(f'{e}')

    return srcs


def split(text: str) -> List[str]:
    return t.split(text, group='sentence')


def tokenize(sentence: str) -> List[str]:
    return t.split(sentence, group='word')


def store_words(words: List[str]) -> None:
    '''
    Adds a list of words to the shelve dictionary
    '''
    with shelve.open(IDF_DB) as db:
        for w in words:
            w = w.lower()  # should words be converted to lowercase?
            if w in db:
                db[w] += 1
            else:
                db[w] = 1


def store_tex(arxiv_id: ArxivID, tex_srcs: List[str]) -> None:
    '''
    Writes the tex source files for an arxiv id to storage.
    '''

    with shelve.open(TEX_DB) as db:
        if arxiv_id in db:
            print(f'{arxiv_id} is already in the db.')
            print('Overwriting...')

        db[arxiv_id] = tex_srcs


def get_downloaded_ids() -> Set[ArxivID]:
    with shelve.open(TEX_DB) as db:
        return set(db.keys())


def main():
    arxiv_ids = list(ids())[0:15]

    stored_ids = get_downloaded_ids()

    print(f'{len(stored_ids)} out of {len(arxiv_ids)} already downloaded.')

    for i in arxiv_ids:
        if i in stored_ids:
            # print(f'{i} has already been stored.')
            continue

        tex_srcs = get_src(i)  # This is the most likely to fail.

        for version in tex_srcs:
            clean_src = detex(version)

            sentences = split(clean_src)

            for s in sentences:
                words = tokenize(s)
                store_words(words)

        store_tex(i, tex_srcs)


if __name__ == '__main__':
    main()
