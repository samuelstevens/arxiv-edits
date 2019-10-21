# Builtin
from typing import List, Tuple
import re
import tarfile
import gzip
import os
import subprocess
import time

# External
import requests
import magic  # type: ignore

# internal
from structures import ArxivID  # type: ignore
from db import connection


def download_file(url: str, local_filename: str) -> str:
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

    return local_filename


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


def analyze_sources(directory, output_file, append=False):
    filenames = sorted(os.listdir(directory))

    with open(output_file, 'a' if append else 'w') as fout:
        for filename in filenames:
            filepath = os.path.join(directory, filename)

            if os.path.isdir(filepath):
                analyze_sources(filepath, output_file, append=True)
            else:
                cmd = f'file -I {filepath}'
                with os.popen(cmd) as fin:
                    result = fin.readlines()
                    for line in result:
                        fout.write(f'{line.strip()}\n')


def download_source_files(arxiv_id: ArxivID, version_count: int, output_directory: str = 'data') -> None:
    '''
    Makes {version_count} network requests, one for each source file, and writest them to {output_directory}
    '''

    for v in range(1, version_count+1):
        url = f'https://arxiv.org/e-print/{arxiv_id}v{v}'
        directory = os.path.join(output_directory, f'{arxiv_id}')
        filename = os.path.join(directory, f'v{v}')

        if not os.path.isdir(directory):
            os.makedirs(directory)

        if not os.path.isfile(filename):
            try:
                download_file(url, filename)
            except requests.exceptions.HTTPError as err:
                print(err)
                print(f'Cannot download source for {arxiv_id}v{v}')

            time.sleep(30)  # respect the server


def get_ids() -> List[Tuple[ArxivID, int]]:
    '''
    Gets 1000 arxiv ids from the local database with multiple versions and returns them as tuple pairs
    '''
    query = 'SELECT arxiv_id, version_count FROM papers WHERE version_count > 1'

    rows = connection().execute(query).fetchall()

    return rows[:1000]  # return only the first 1000


if __name__ == '__main__':
    ARXIV_ID_PAIRS = get_ids()

    # for arxiv_id, version_count in ARXIV_ID_PAIRS:
    #     download_source_files(arxiv_id, version_count)

    source_type_file = os.path.join('data', 'initial_types.txt')
    directory = os.path.join('data', 'source_files')
    analyze_sources(directory, source_type_file)
