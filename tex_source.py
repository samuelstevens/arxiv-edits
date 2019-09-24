# Builtin
from typing import List
import re
import tarfile
import os

# External
import requests


def download_file(url: str, local_filename: str) -> str:
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()
    return local_filename


VERSION_PATTERN = re.compile(r'\[v(.)\]')


def get_text(arxiv_id: str, clean=False) -> List[str]:

    # 3. download those versions.

    tex_sources = []

    abs_url = f'https://arxiv.org/abs/{arxiv_id}'

    # 1. get the https://arxiv.org/abs/ page
    with requests.get(abs_url) as r:
        r.raise_for_status()
        abs_page = r.text

    # 2. find all the version tags on the page.
    versions = VERSION_PATTERN.findall(abs_page)

    if len(versions) < 2:  # not multiple versions
        return tex_sources

    # for each version:
    for v in versions:
        url = f'https://arxiv.org/e-print/{arxiv_id}v{v}'
        filename = f'{arxiv_id}v{v}'
        # 1. download vX to the local filesystem
        if not os.path.isfile(filename):
            download_file(url, filename)

        # 2. get the longest .tex file in each tar
        with tarfile.open(filename) as tar:
            tex_source: str = ''
            for tarinfo in tar:
                if os.path.splitext(tarinfo.name)[1] == ".tex":
                    f = tar.extractfile(tarinfo)
                    contents: str = f.read().decode()
                    if len(contents) > len(tex_source):
                        tex_source = contents

        tex_sources.append(tex_source)

        if clean and os.path.isfile(filename):
            os.remove(filename)

    return tex_sources
