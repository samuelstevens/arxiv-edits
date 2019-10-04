# builtin
from typing import List, Tuple

# external
import requests
import nltk.data

# Internal
from tex import download_tex_src, detex
from macro_align import parse_sections
from database import connection
from sentence_splitter import splitter

detex('hello')


def valid_ids():
    query = 'SELECT arxiv_id FROM papers WHERE multiple_versions = 1'
    con = connection()
    con.row_factory = lambda cursor, row: row[0]
    ids = con.execute(query)

    return ids


# TODO
def looked_at(arxiv_s):
    return False


def magic_tuple(tuple):
    tuple


def main():

    ids = valid_ids()

    # t = splitter()

    for i in ids:
        # 1. check if s has been checked already
        if looked_at(i):
            # 2. if it has, move on
            continue

        # 3. if it has not, download the text
        try:
            version_sources = download_tex_src(i)

            if len(version_sources) < 2:  # not more than one version
                continue

            # macro align the sections
            version_sections = parse_sections(version_sources)

            # remove all tex source leftovers
            version_sections = [tuple([detex(v) for v in section_tuple])
                                for section_tuple in version_sections]

            print(version_sections[0][0])

        except requests.exceptions.HTTPError as e:
            # page does not exist
            print(e)

        break


main()
