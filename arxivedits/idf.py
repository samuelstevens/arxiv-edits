'''
Provides functionality to write documents to a persistent dictionary (via `shelve`) that can be queried with `idf()`.
'''

import shelve
import os
import json
from math import log

from db import IDF_DB
from nlp import ArxivTokenizer

TOTALDOCS = len(os.listdir(os.path.join('data', 'unzipped')))

TOKENIZER = ArxivTokenizer()

DOCUMENTFREQUENCY = None


def initialize_idf():
    '''
    Initializes the global document frequency dictionary for repeated accesses.

    TODO: need to write a way to close.
    '''
    global DOCUMENTFREQUENCY
    DOCUMENTFREQUENCY = shelve.open(IDF_DB)


def idf(word: str) -> float:
    '''
    Returns the inverse document frequency of a word
    '''
    global DOCUMENTFREQUENCY
    numerator = 1 + TOTALDOCS

    if not word:
        print(f'Word {word} not a string.')
        return 0

    if not DOCUMENTFREQUENCY:
        initialize_idf()

    if word not in DOCUMENTFREQUENCY:
        # print(f'Word {word} not in document frequency.')
        return 0

    denominator = 1 + DOCUMENTFREQUENCY[word]

    return log(numerator / denominator)  # natural log


def add_doc(inputfile):
    '''
    Adds all the words in a json file to the IDF_DB.

    TODO: might need to optimize the repeated call to `shelve.open`
    '''
    added_words = set()
    with open(inputfile, 'r') as file:
        sections = json.load(file)

    for _, _, content in sections:
        words = TOKENIZER.split(content, group='word')
        # print(f'{inputfile} has {len(words)} words.')

        with shelve.open(IDF_DB) as documentfrequency:
            for word in words:
                if word not in added_words:
                    if word in documentfrequency:
                        documentfrequency[word] += 1
                    else:
                        documentfrequency[word] = 1
                    added_words.add(word)


def main():
    '''
    Resets the IDF_DB with every file in data/sections
    '''
    if os.path.isfile(IDF_DB):
        os.remove(IDF_DB)

    sectionfiles = os.path.join('data', 'sections')

    for sectionfile in os.listdir(sectionfiles):
        sectionfilepath = os.path.join(sectionfiles, sectionfile)
        add_doc(sectionfilepath)


if __name__ == '__main__':
    main()
