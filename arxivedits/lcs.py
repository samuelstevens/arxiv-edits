'''
Implements and exports a weighted-LCS algorithm.
'''
import shelve
from math import inf
from typing import List, Optional, TypeVar
from nlp import ArxivTokenizer
from idf import idf

TOKENIZER = ArxivTokenizer()


DOCUMENTFREQ: Optional[shelve.DbfilenameShelf] = None

Generic = TypeVar('T')


def lcs(seq1: List[Generic], seq2: List[Generic]) -> List[Generic]:
    '''
    longest common subsequence, inspired by https://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Worked_example
    '''

    if not seq1 or not seq2:
        return []

    table: List[List[List[Generic]]] = [[[]
                                         for i in range(len(seq2))] for j in range(len(seq1))]  # this might be really, really inefficient

    for i, _ in enumerate(seq1):
        for j, _ in enumerate(seq2):
            if seq1[i] == seq2[j]:
                prevrecord = table[i-1][j-1] if i > 0 and j > 0 else []

                table[i][j] = prevrecord + [seq2[j]]
            else:
                # this is dangerous when i == 0 or j == 0, because we're accessing table[-1] (which is valid in python)
                # in addition, we are not creating a new list here. It's especially difficult because the table's data structure is also mutable.
                table[i][j] = max(table[i][j-1], table[i-1][j], key=len)

    return table[-1][-1]


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
        return -inf

    return numerator / denominator


def main():
    '''
    Demonstrates `lcs()` and `similarity()`.
    '''
    def lcs_of_sentence(sentence1, sentence2):
        words1 = TOKENIZER.split(sentence1, group='word')
        words2 = TOKENIZER.split(sentence2, group='word')
        return lcs(words1, words2)

    sample1 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample2 = "The long-sought Higgs boson particle will be observed at CERN."

    sample3 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."
    sample4 = "It can not be determined correctly."

    sample5 = "A precise theoretical understanding of the kinematic distributions for diphoton production in the standard model could provide valuable guidance in the search for the Higgs boson signal and assist in the important measurement of Higgs boson coupling strengths."
    sample6 = "The long-sought Higgs boson may soon be observed at the CERN Large Hadron."

    print(sample1)
    print(lcs_of_sentence(sample1, sample2))
    print(similarity(sample1, sample2))

    print(sample3)
    print(lcs_of_sentence(sample3, sample4))
    print(similarity(sample3, sample4))

    print(sample5)
    print(lcs_of_sentence(sample5, sample6))
    print(similarity(sample5, sample6))

    print(lcs_of_sentence('Introduction', 'Introduction'))
    print(similarity('Introduction', 'Introduction'))


if __name__ == '__main__':
    main()
