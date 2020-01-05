'''
Implements and exports a weighted-LCS algorithm.

gcc -c -Wall -Werror -fpic arxivedits/lcs.c -o arxivedits/lcs.o
gcc -shared -o arxivedits/lcs.so arxivedits/lcs.o
'''
import shelve
import cProfile
import pathlib
import os
import ctypes

from math import inf
from typing import List, Optional, TypeVar, Dict, Tuple
from tokenizer import ArxivTokenizer
from idf import idf

TOKENIZER = ArxivTokenizer()
DOCUMENTFREQ: Optional[shelve.DbfilenameShelf] = None

T = TypeVar('T')  # pylint: disable=invalid-name
pwd = pathlib.Path(__file__).parent  # pylint: disable=invalid-name


class CELL(ctypes.Structure):
    '''
    struct Cell
    {
        int index;
        int length;
        struct Cell *prev;
    };
    '''


# pylint: disable=protected-access
CELL._fields_ = [('index', ctypes.c_int), ('length', ctypes.c_int),
                 ('prev', ctypes.POINTER(CELL))]


class SEQUENCE(ctypes.Structure):
    '''
    ```
    struct Sequence
    {
        char **items;
        int length;
    };
    ```
    '''
    _fields_ = [('items', ctypes.POINTER(ctypes.c_char_p)),
                ('length', ctypes.c_int)]


lcsmodule = ctypes.cdll.LoadLibrary(
    os.path.join(pwd, 'lcsmodule', 'lcs.so'))
lcsmodule.lcs.restype = ctypes.POINTER(SEQUENCE)


def slow_lcs(seq1: List[T], seq2: List[T]) -> List[T]:
    '''
    longest common subsequence, inspired by https://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Worked_example
    '''

    if not seq1 or not seq2:
        return []

    table: Dict[Tuple[int, int], List[int]] = {}
    for i, _ in enumerate(seq1):
        for j, _ in enumerate(seq2):

            if seq1[i] == seq2[j]:
                table[(i, j)] = table[(i-1, j-1)] + \
                    [j] if i > 0 and j > 0 else [j]
            else:
                # this is dangerous when i == 0 or j == 0, because we're accessing table[-1] (which is valid in python)
                # in addition, we are not creating a new list here. It's especially difficult because the table's data structure is also mutable.
                # table[i][j] = max(table[i][j-1], table[i-1][j], key=len)
                table[(i, j)] = []
                if i > 0:
                    table[(i, j)] = table[(i-1, j)]

                if j > 0:
                    if len(table[(i, j-1)]) > len(table[(i, j)]):
                        table[(i, j)] = table[(i, j-1)]

    finalsequence = table[(len(seq1) - 1, len(seq2) - 1)]

    return [seq2[j] for j in finalsequence]


def list_to_SEQUENCE(strlist: List[str]) -> SEQUENCE:
    '''
    Converts a list of strings to a sequence struct
    '''
    bytelist = [bytes(s, 'utf-8') for s in strlist]
    arr = (ctypes.c_char_p * len(bytelist))()
    arr[:] = bytelist
    return SEQUENCE(arr, len(bytelist))


def lcs(s1: List[str], s2: List[str]) -> List[str]:
    '''
    Fast LCS that uses ctypes
    '''
    seq1 = list_to_SEQUENCE(s1)
    seq2 = list_to_SEQUENCE(s2)

    common = lcsmodule.lcs(ctypes.byref(seq1), ctypes.byref(seq2))[0]

    ret = []

    for i in range(common.length):
        ret.append(common.items[i].decode('utf-8'))
    lcsmodule.freeSequence(common)

    return ret


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


def profile():
    cProfile.run('lcs_many()', sort='tottime')


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
    # main()
    profile()
    # fast_lcs(
    #     ['First', ',', 'we', 'validate', 'whether', 'our', 'models', 'for', 'segmentation', 'and', 'depth', 'estimation',
    #         'perform', 'well', 'on', 'the', 'synthetic', 'test', 'set', 'of', 'our', 'SURREAL', 'dataset', '.'],
    #     ['Segmentation', 'and', 'depth', 'are', 'tested', 'on', 'the', 'synthetic', 'and', 'Human3.6M', 'test', 'sets',
    #         'with', 'networks', 'pre-trained', 'on', 'a', 'subset', 'of', 'the', 'synthetic', 'training', 'data', '.']
    # )
