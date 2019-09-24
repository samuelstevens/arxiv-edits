
from datetime import date
import requests
from typing import List
from bs4 import BeautifulSoup
import re


def looked_at(arxiv_s):
    return False


def get_max_number(year, month):
    if year < 15:
        return (9999, 4)

    return(99999, 5)


def arxiv_identifiers():
    today = date.today()
    today_year = today.year % 100  # will produce 19, 20, etc.

    year = 7
    month = 4
    number = 1

    max_number, digits = get_max_number(year, month)

    while year <= today_year:
        while month <= 12:
            while number < max_number:
                yield f'{year:02}{month:02}.{number:0{digits}}'
                number += 1
            month += 1
            number = 1
            max_number, digits = get_max_number(year, month)
        year += 1
        month = 1


def download_file(url, local_filename):
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


version_pattern = re.compile('\[v(.)\]')


def get_text(id: str) -> List[str]:

    # 3. download those versions.

    tex_sources = []

    abs_url = f'https://arxiv.org/abs/{id}'

    # 1. get the https://arxiv.org/abs/ page
    with requests.get(abs_url) as r:
        r.raise_for_status()
        abs_page = r.text

    # 2. find all the version tags on the page.
    versions = version_pattern.findall(abs_page)

    # for each version:
    for v in versions:
        url = f'https://arxiv.org/e-print/{id}v{v}'
        filename = f'{id}v{v}'
        # 1. download vX to the local filesystem
        download_file(url, filename)

        # 2. unzip vX
        # run `mkdir -p vX && tar -xvf filename
        # 3. find the .tex file
        # 4. add the .tex source to the list to return
        # 5. delete all the local files

    return tex_sources


def main():
    identifiers = arxiv_identifiers()

    identifiers = ['0704.0002', '0801.9999']  # one valid, one invalid

    for id in identifiers:
        # check if s has been checked already
        # if it has, move on
        # if it has not, download the text

        if looked_at(id):
            continue

        try:
            text = get_text(id)
        except requests.exceptions.HTTPError as e:
            # page does not exist
            print(e)


main()
