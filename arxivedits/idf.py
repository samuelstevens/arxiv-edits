"""
Provides functionality to write documents to a persistent dictionary (via `shelve`) that can be queried with `idf()`.
"""

import shelve
import os
import json
import cProfile
import functools
from math import log
from typing import Set

from massalign.core import TFIDFModel

import data
from tokenizer import ArxivTokenizer

TOTALDOCS = 307

TOKENIZER = ArxivTokenizer()

DOCUMENTFREQUENCY = shelve.open(data.IDF_DB)

# inputfiles = map(lambda f: os.path.join(data.TEXT_DIR, f), os.listdir(data.TEXT_DIR))

# TFIDFMODEL = TFIDFModel(
#     input_files=inputfiles,
#     stop_list="https://ghpaetzold.github.io/massalign_data/stop_words.txt",
# )


def initialize_idf():
    """
    Initializes the global document frequency dictionary for repeated accesses.

    TODO: need to write a way to close.
    """
    global DOCUMENTFREQUENCY
    DOCUMENTFREQUENCY = shelve.open(data.IDF_DB)


@functools.lru_cache(maxsize=512)
def idf(word: str) -> float:
    """
    Returns the inverse document frequency of a word
    """
    numerator = 1 + TOTALDOCS

    if not word:
        # print(f'Word {word} not a string.')
        return 0

    while not DOCUMENTFREQUENCY:
        initialize_idf()

    if word not in DOCUMENTFREQUENCY:
        # print(f'Word {word} not in document frequency.')
        return 0

    denominator = 1 + DOCUMENTFREQUENCY[word]

    return log(numerator / denominator)  # natural log


def add_doc(sectionfile: str):
    """
    Adds all the words in a json file to the IDF_DB.

    TODO: might need to optimize the repeated call to `shelve.open`
    """
    addedwords: Set[str] = set()
    with open(sectionfile, "r") as file:
        sections = json.load(file)

    for title, content in sections:
        words = TOKENIZER.split(content, group="word")
        words.extend(TOKENIZER.split(title, group="word"))
        # print(f'{inputfile} has {len(words)} words.')

        with shelve.open(data.IDF_DB) as documentfrequency:
            for word in words:
                if word not in addedwords:
                    if word in documentfrequency:
                        documentfrequency[word] += 1
                    else:
                        documentfrequency[word] = 1
                    addedwords.add(word)


def profile():
    cProfile.run("idf('our')", sort="tottime")


def main():
    """
    Resets the IDF_DB with every file in data/sections
    """
    if os.path.isfile(data.IDF_DB):
        os.remove(data.IDF_DB)

    for sectionfile in os.listdir(data.SECTIONS_DIR):
        sectionfilepath = os.path.join(data.SECTIONS_DIR, sectionfile)
        add_doc(sectionfilepath)


if __name__ == "__main__":
    profile()
