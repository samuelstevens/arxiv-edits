# Builtin
from typing import List
import re
import tarfile
import gzip
import os
import subprocess

# internal
from structures import ArxivID  # type: ignore

# External
import requests
import magic  # type: ignore


def download_file(url: str, local_filename: str) -> str:
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

    # NOTE the stream=True parameter below
    # print(f'Downloading {url}...')
    with requests.get(url, stream=True) as r:

        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()

    # print(f'Saved to {local_filename}')
    return local_filename


VERSION_PATTERN = re.compile(r'\[v(.)\]')

SOURCE_PATTERN = re.compile(r'<a href="/e-print/\d+\.\d+">Source</a>')

COOKIES = {'xxx-ps-defaults': 'src'}


def download_tex_src(arxiv_id: ArxivID, clean=False, directory='data') -> List[str]:
    tex_sources: List[str] = []

    abs_url = f'https://arxiv.org/abs/{arxiv_id}'

    # 1. get the https://arxiv.org/abs/ page
    print(f'Getting {abs_url}')
    with requests.get(abs_url, cookies=COOKIES) as r:
        r.raise_for_status()
        abs_page = r.text

    # 1.5 check if source is available.
    source_available = SOURCE_PATTERN.search(abs_page)

    if not source_available:
        print(f'Source for {arxiv_id} not available.')
        return tex_sources

    # 2. find all the version tags on the page.
    versions = VERSION_PATTERN.findall(abs_page)

    # for each version:
    for v in versions:
        url = f'https://arxiv.org/e-print/{arxiv_id}v{v}'
        filename = os.path.join(directory, f'{arxiv_id}v{v}')

        if not os.path.isdir(directory):
            os.makedirs(directory)

        # 1. download vX to the local filesystem
        if not os.path.isfile(filename):
            download_file(url, filename)

        # 2. gunzip the .gz
        with gzip.open(filename) as gz:
            tex_source: str = ''

            filetype: str = magic.from_buffer(gz.read(1024))

            if 'ASCII' in filetype:
                tex_source = gz.read().decode()
            elif 'UTF-8' in filetype:
                tex_source = gz.read().decode('utf_8', errors='replace')
            elif 'tar' in filetype:
                # 3. get the longest .tex file in each tar
                tex_source = get_longest_tex(filename)
            else:
                print(f'Not sure what type {filetype} is.')

        tex_sources.append(tex_source)

        if clean and os.path.isfile(filename):
            os.remove(filename)

    return tex_sources


def get_longest_tex(filename) -> str:
    tex = ''
    with tarfile.open(filename) as tar:
        for tarinfo in tar:
            if os.path.splitext(tarinfo.name)[1] == ".tex":
                f = tar.extractfile(tarinfo)
                if f:
                    contents: str = f.read().decode()
                    if len(contents) > len(tex):
                        tex = contents

    return tex


def detex(text: str) -> str:

    try:
        result = subprocess.run(['detex', '-r'], text=True,
                                input=text, capture_output=True)
        return result.stdout
    except AttributeError:
        print(
            f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes).")
        return ''
