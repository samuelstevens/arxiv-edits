# Builtin
from typing import List, Tuple, Optional
import tarfile
import gzip
import os
import time

# External
import requests
import magic  # type: ignore

# internal
from structures import ArxivID  # type: ignore
from db import connection

SOURCE_DIR = os.path.join('data', 'source_files')
EXTRACTED_DIR = os.path.join('data', 'unzipped')


def download_file(url: str, local_filename: str) -> str:
    '''
    Downloads a file by streaming it. Taken from # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    '''

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with open(local_filename, 'wb') as file:
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    file.write(chunk)

    return local_filename


def longest_tex_from_tar(tar: tarfile.TarFile) -> str:
    '''
    Takes a directory and returns the longest .tex files contents
    '''

    tex = b''

    for member in tar.getmembers():
        if member.isfile() and os.path.splitext(member.name)[1] == ".tex":
            file = tar.extractfile(member)
            contents = file.read()

            if len(contents) > len(tex):
                tex = contents

    return tex


def longest_tex_from_dir(directory: str) -> str:
    '''
    Returns the contents of the longest .tex file in a directory as a string.
    '''
    tex = ''
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)

        if os.path.isdir(path):
            # recursively search
            contents = longest_tex_from_dir(path)

            if len(contents) > len(tex):
                tex = contents

        elif os.path.splitext(filename)[1] == ".tex":
            with open(os.path.join(directory, filename), 'r') as file:
                contents = file.read()
                if len(contents) > len(tex):
                    tex = contents
    return tex


def get_filetype(file):
    '''
    returns the filetype of a file using magic (file utility on unix). Resets the file pointer to the start of the file.
    '''
    file.seek(0)  # ensures that we read the first 1024 bytes
    buffer = file.read(1024)
    file.seek(0)  # resets the position to the start.
    return magic.from_buffer(buffer, mime=True)


def extract(in_dir, filename) -> Optional[bytes]:
    '''
    Takes a filepath (dir, name) and extracts the longest .tex file, then returns the contents as a string.
    TODO
    '''

    os.makedirs('tmp', exist_ok=True)
    filepath = os.path.join(in_dir, filename)

    if os.path.isdir(filepath):
        return longest_tex_from_dir(filepath)

    # now, filepath is not a directory
    with open(filepath, 'rb') as file:
        while True:
            file.seek(0)
            filetype = get_filetype(file)

            if 'gzip' in filetype:
                # print(f'Using gunzip to unzip {filename}.')
                file = gzip.open(file, 'rb')

            elif 'pdf' in filetype:
                # print('Going to ignore PDF.')
                return None

            elif 'tar' in filetype:
                # print(f'Using tar to extract from {filename}')
                with tarfile.open(fileobj=file, mode='r') as tar:
                    return longest_tex_from_tar(tar)
            elif 'tex' in filetype:
                # print(f'Reading directly from {filename}')
                return file.read()

            else:
                raise TypeError(f'{filetype} not implemented yet.')


def download_source_files(arxiv_id: ArxivID, version_count: int, output_directory: str = 'data') -> None:
    '''
    Makes {version_count} network requests, one for each source file, and writest them to {output_directory}
    '''

    for version in range(1, version_count+1):
        url = f'https://arxiv.org/e-print/{arxiv_id}v{version}'
        filename = os.path.join(output_directory, f'{arxiv_id}-v{version}')

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        if not os.path.isfile(filename):
            try:
                download_file(url, filename)
            except requests.exceptions.HTTPError as err:
                print(err)
                print(f'Cannot download source for {arxiv_id}v{version}')

            time.sleep(30)  # respect the server


def get_ids() -> List[Tuple[ArxivID, int]]:
    '''
    Gets 1000 arxiv ids from the local database with multiple versions and returns them as tuple pairs
    '''
    query = 'SELECT arxiv_id, version_count FROM papers WHERE version_count > 1'

    rows = connection().execute(query).fetchall()

    return rows[:1000]  # return only the first 1000


def download_all():
    '''
    Downloads all source files for all versions for all papers with 2+ versions.
    '''
    arxiv_id_pairs = get_ids()

    for arxiv_id, version_count in arxiv_id_pairs:
        download_source_files(arxiv_id, version_count, SOURCE_DIR)


def extract_all():
    '''
    Extracts the longest .tex file from every file in SOURCE_DIR to UNZIPPED_DIR
    '''

    os.makedirs(EXTRACTED_DIR, exist_ok=True)

    for filename in os.listdir(SOURCE_DIR):
        try:
            content = extract(SOURCE_DIR, filename)

        except TypeError as err:
            print(err)

        if content:
            # removes not utf characters
            content = content.decode(
                'utf-8', errors='ignore').encode(encoding='utf-8', errors='ignore')
            with open(os.path.join(EXTRACTED_DIR, filename), 'wb') as file:
                file.write(content)


if __name__ == '__main__':
    # download_all()
    extract_all()
