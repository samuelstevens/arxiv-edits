'''
Implements and exports a weighted-LCS algorithm.
'''
import shelve
import os
from math import log  # natural log
from typing import List, Optional, TypeVar
from nlp import ArxivTokenizer
from db import IDF_DB

TOKENIZER = ArxivTokenizer()

TOTALDOCS = len(os.listdir(os.path.join('data', 'unzipped')))

DOCUMENTFREQ: Optional[shelve.DbfilenameShelf] = None

Type = TypeVar('T')


def idf(word: str) -> float:
    '''
    Returns the inverse document frequency of a word
    '''
    numerator = 1 + TOTALDOCS

    if not word:
        print(f'Word {word} not a string.')
        return -1 * float('inf')

    if not DOCUMENTFREQ or word not in DOCUMENTFREQ:
        print(f'Word {word} not in document frequency.')
        return -1 * float('inf')

    denominator = 1 + DOCUMENTFREQ[word]

    return log(numerator / denominator)  # natural log


def lcs(seq1: List[Type], seq2: List[Type]) -> List[Type]:
    '''
    longest common subsequence, inspired by https://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Worked_example
    '''

    table: List[List[List[Type]]] = [[[]] * (len(seq2) + 1)] * (len(seq1) + 1)

    for i in range(len(seq1)):
        for j in range(len(seq2)):
            if i == 0 or j == 0:
                table[i][j] = []
            elif seq1[i] == seq2[j]:
                table[i][j] = max(table[i][j-1], table[i-1]
                                  [j], key=len) + [seq2[j]]
            else:
                table[i][j] = max(table[i][j-1], table[i-1][j], key=len)

    return table[len(seq1) - 1][len(seq2) - 1]


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

    sample_lcs1 = ['Hi', 'my', 'name', 'is', 'Sam']
    sample_lcs2 = ['Hello', 'my', 'name', 'is', 'Steve',
                   'or', 'you', 'can', 'call', 'me', 'Sam']

    print(lcs(sample_lcs1, sample_lcs2))

    sample1 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample2 = "The long-sought Higgs boson particle will be observed at CERN."

    sample3 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample4 = "It can not be determined correctly."

    sample5 = "A precise theoretical understanding of the kinematic distributions for diphoton production in the standard model could provide valuable guidance in the search for the Higgs boson signal and assist in the important measurement of Higgs boson coupling strengths."
    sample6 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."

    print(similarity(sample1, sample2))
    print(similarity(sample3, sample4))
    print(similarity(sample5, sample6))

    DOCUMENTFREQ.close()


if __name__ == '__main__':
    main()
