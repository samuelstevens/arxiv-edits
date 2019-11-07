import shelve
import os
from math import log

from db import IDF_DB
from nlp import ArxivTokenizer

TOTALDOCS = len(os.listdir(os.path.join('data', 'unzipped')))

tokenizer = ArxivTokenizer()


def idf(word: str) -> float:
    '''
    Returns the inverse document frequency of a word
    '''
    numerator = 1 + TOTALDOCS

    if not word:
        print(f'Word {word} not a string.')
        return 0

    with shelve.open(IDF_DB) as documentfrequency:
        if word not in documentfrequency:
            print(f'Word {word} not in document frequency.')
            return 0

        denominator = 1 + documentfrequency[word]

    return log(numerator / denominator)  # natural log


def adddoc(inputfile):
    added_words = set()
    with open(inputfile, 'r') as file:
        content = file.read()

    words = tokenizer.split(content, group='word')
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
    os.remove(IDF_DB)

    textfiles = os.path.join('data', 'text')

    for textfile in os.listdir(textfiles):
        textfilepath = os.path.join(textfiles, textfile)
        adddoc(textfilepath)


if __name__ == '__main__':
    main()
