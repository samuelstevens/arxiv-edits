# builtin
from typing import List, Tuple
import difflib

# external
import requests
import nltk.data

# Internal
from tex import download_tex_src, detex
from align import parse_sections
from db import connection
from sentences import Splitter
from structures import ArxivID


def valid_ids() -> List[ArxivID]:
    query = 'SELECT arxiv_id FROM papers WHERE multiple_versions = 1'
    con = connection()
    con.row_factory = lambda cursor, row: row[0]
    ids = con.execute(query)

    return ids


# TODO
def looked_at(i: ArxivID) -> bool:
    return False


def main():

    ids = valid_ids()

    t = Splitter()

    for i in ids:
        # 1. check if s has been checked already
        if looked_at(i):
            # 2. if it has, move on
            continue

        # 3. if it has not, download the text
        try:
            version_sources = download_tex_src(i)

            # macro align the sections
            versioned_sections = parse_sections(version_sources)

            # remove all tex source leftovers
            versioned_sections = [tuple([detex(v) for v in section_tuple])
                                  for section_tuple in versioned_sections]

            # print(len(versioned_sections), len(versioned_sections[0]))

            for section_tuple in versioned_sections:
                # section_tuple is a tuple of the versions of each section
                sentences_v1 = t.split(section_tuple[0])
                sentences_v2 = t.split(section_tuple[1])

                # sentences_v3 = t.split(section_tuple[2])
                break

        except requests.exceptions.HTTPError as e:
            # page does not exist
            print(e)

        break


main()
