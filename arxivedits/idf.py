from typing import List, Set
import shelve
import os

from db import connection, TEX_DB, IDF_DB
from nlp import ArxivTokenizer

import requests

t = ArxivTokenizer()


def split(text: str) -> List[str]:
    return t.split(text, group='sentence')


def tokenize(sentence: str) -> List[str]:
    return t.split(sentence, group='word')


def adddoc(inputfile):
    added_words = set()
    with open(inputfile, 'r') as f:
        content = f.read()

    words = tokenize(content)
    print(f'{inputfile} has {len(words)} words.')

    with shelve.open(IDF_DB) as idf:
        for word in words:
            if word not in added_words:
                if word in idf:
                    idf[word] += 1
                else:
                    idf[word] = 1
                added_words.add(word)


if __name__ == '__main__':
    textfiles = os.path.join('data', 'text')

    for textfile in os.listdir(textfiles):
        textfilepath = os.path.join(textfiles, textfile)
        adddoc(textfilepath)
