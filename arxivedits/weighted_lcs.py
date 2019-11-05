'''
Implements and exports a weighted-LCS algorithm.
'''
import shelve
import os
from math import log  # natural log
from typing import List, Any
from nlp import ArxivTokenizer
from db import IDF_DB

TOKENIZER = ArxivTokenizer()

TOTALDOCS = len(os.listdir(os.path.join('data', 'unzipped')))

DOCUMENTFREQ = {}


def idf(word) -> float:
    '''
    Returns the inverse document frequency of a word
    '''
    numerator = 1 + TOTALDOCS

    if word not in DOCUMENTFREQ:
        print(f'Word {word} not in document frequency.')
        return -1 * float('inf')

    denominator = 1 + DOCUMENTFREQ[word]

    return log(numerator / denominator)  # natural log


def lcs(sequence1: List[Any], sequence2: List[Any]) -> List[Any]:
    '''
    Naive implementation of longest common subsequence. Implemented with an explanation from https://www.geeksforgeeks.org/longest-common-subsequence-dp-4/
    '''
    if not sequence1 or not sequence2:
        return []

    if sequence1[-1] == sequence2[-1]:
        return lcs(sequence1[:-1], sequence2[:-1]) + [sequence1[-1]]

    version1 = lcs(sequence1[:-1], sequence2)
    version2 = lcs(sequence1, sequence2[:-1])

    if len(version1) > len(version2):
        return version1

    return version2


def similarity(sentence1: str, sentence2: str) -> float:
    '''
    Uses an idf-weighted longest common subsequence algorithm to find the similarity between two English sentences. Returns -Infinity if there is an error.
    '''
    words1 = TOKENIZER.split(sentence1, group='word')
    words2 = TOKENIZER.split(sentence2, group='word')

    numerator = sum([idf(word) for word in lcs(words1, words2)])

    denominator = max(sum([idf(word) for word in words1]),
                      sum([idf(word) for word in words2]))

    if denominator == 0:
        print('Denominator was 0.')
        return float('inf') * -1

    return numerator / denominator


def main():
    global DOCUMENTFREQ
    DOCUMENTFREQ = shelve.open(IDF_DB)

    sample1 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample2 = "The long-sought Higgs boson particle will be observed at CERN."

    sample3 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample4 = "It can not be determined correctly."

    print(similarity(sample1, sample2))
    print(similarity(sample3, sample4))

    DOCUMENTFREQ.close()


if __name__ == '__main__':
    main()
