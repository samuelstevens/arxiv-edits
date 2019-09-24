# external
import requests


# Internal
from tex_source import get_text
from arxiv_util import arxiv_ids
from macro_align import parse_sections


def looked_at(arxiv_s):
    return False


def main():
    ids = arxiv_ids()

    # for testing purposes
    ids = ['0704.0002', '0801.9999']  # one valid, one invalid

    for i in ids:
        # 1. check if s has been checked already
        if looked_at(i):
            # 2. if it has, move on
            continue

        # 3. if it has not, download the text
        try:
            version_sources = get_text(i)

            if len(version_sources) < 2:  # not more than one version
                continue

            # macro align the sections
            version_sections = parse_sections(version_sources)

        except requests.exceptions.HTTPError as e:
            # page does not exist
            print(e)


main()
