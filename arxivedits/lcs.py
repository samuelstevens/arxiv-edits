"""
Implements and exports a weighted-LCS algorithm.

gcc -c -Wall -Werror -O3 -fpic arxivedits/lcsmodule/lcs.c -o arxivedits/lcsmodule/lcs.o
gcc -shared -o arxivedits/lcsmodule/lcs.so arxivedits/lcsmodule/lcs.o
"""
import cProfile
import pathlib
import os
import ctypes

from typing import List, TypeVar, Dict, Tuple


T = TypeVar("T")  # pylint: disable=invalid-name
pwd = pathlib.Path(__file__).parent  # pylint: disable=invalid-name


class SEQUENCE(ctypes.Structure):
    """
    ```
    struct Sequence
    {
        char **items;
        int length;
    };
    ```
    """

    _fields_ = [("items", ctypes.POINTER(ctypes.c_char_p)), ("length", ctypes.c_int)]


lcsmodule = ctypes.cdll.LoadLibrary(os.path.join(pwd, "lcsmodule", "lcs.so"))
lcsmodule.lcs.restype = ctypes.POINTER(SEQUENCE)


def slow_lcs(seq1: List[T], seq2: List[T]) -> List[T]:
    """
    longest common subsequence, inspired by https://en.wikipedia.org/wiki/Longest_common_subsequence_problem#Worked_example
    """

    if not seq1 or not seq2:
        return []

    table: Dict[Tuple[int, int], List[int]] = {}
    for i, _ in enumerate(seq1):
        for j, _ in enumerate(seq2):

            if seq1[i] == seq2[j]:
                table[(i, j)] = table[(i - 1, j - 1)] + [j] if i > 0 and j > 0 else [j]
            else:
                # this is dangerous when i == 0 or j == 0, because we're accessing table[-1] (which is valid in python)
                # in addition, we are not creating a new list here. It's especially difficult because the table's data structure is also mutable.
                # table[i][j] = max(table[i][j-1], table[i-1][j], key=len)
                table[(i, j)] = []
                if i > 0:
                    table[(i, j)] = table[(i - 1, j)]

                if j > 0:
                    if len(table[(i, j - 1)]) > len(table[(i, j)]):
                        table[(i, j)] = table[(i, j - 1)]

    finalsequence = table[(len(seq1) - 1, len(seq2) - 1)]

    return [seq2[j] for j in finalsequence]


def list_to_SEQUENCE(strlist: List[str]) -> SEQUENCE:
    """
    Converts a list of strings to a sequence struct
    """
    bytelist = [bytes(s, "utf-8") for s in strlist]
    arr = (ctypes.c_char_p * len(bytelist))()
    arr[:] = bytelist
    return SEQUENCE(arr, len(bytelist))


def lcs(s1: List[str], s2: List[str]) -> List[str]:
    """
    Fast LCS that uses ctypes
    """
    seq1 = list_to_SEQUENCE(s1)
    seq2 = list_to_SEQUENCE(s2)

    common = lcsmodule.lcs(ctypes.byref(seq1), ctypes.byref(seq2))[0]

    ret = []

    for i in range(common.length):
        ret.append(common.items[i].decode("utf-8"))
    lcsmodule.freeSequence(common)

    return ret


def profile():
    cProfile.run("lcs_many()", sort="tottime")

    # profile()
    # fast_lcs(
    #     ['First', ',', 'we', 'validate', 'whether', 'our', 'models', 'for', 'segmentation', 'and', 'depth', 'estimation',
    #         'perform', 'well', 'on', 'the', 'synthetic', 'test', 'set', 'of', 'our', 'SURREAL', 'dataset', '.'],
    #     ['Segmentation', 'and', 'depth', 'are', 'tested', 'on', 'the', 'synthetic', 'and', 'Human3.6M', 'test', 'sets',
    #         'with', 'networks', 'pre-trained', 'on', 'a', 'subset', 'of', 'the', 'synthetic', 'training', 'data', '.']
    # )
