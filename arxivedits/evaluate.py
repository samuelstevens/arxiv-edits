'''
Evaluates MASSAlign vs weighted-LCS on a manually aligned dataset
'''

import csv
import os
import pathlib
import json
from typing import Tuple, Callable, List, Dict

import Levenshtein as fast_levenshtein
import data
import align

Algorithm = Callable[[List[str], List[str]], List[Tuple[int, int]]]


class Evaluation:
    '''
    True/false positive/negative results for an algorithm
    '''

    def __init__(self, algorithm: Algorithm):
        self.algorithm = algorithm
        self.TP = 0
        self.FP = 0
        self.TN = 0
        self.FN = 0
        self.precision = 0
        self.recall = 0
        self.f1 = 0

    def add_results(self, TP: int, FP: int, TN: int, FN: int):
        '''
        Adds a number of true/false positive/negative results
        '''
        self.TP += TP
        self.FP += FP
        self.TN += TN
        self.FN += FN

        if self.TP + self.FP > 0:
            self.precision = self.TP / (self.TP + self.FP)
        if self.TP + self.FN > 0:
            self.recall = self.TP / (self.TP + self.FN)
        if self.precision + self.recall > 0:
            self.f1 = 2 * (self.precision * self.recall) / \
                (self.precision + self.recall)

    def display(self, verbose=False):
        '''
        Displays results to stdout
        '''
        print(self.algorithm.__name__)
        if verbose:
            print(f'TP: {self.TP}')
            print(f'FP: {self.FP}')
            print(f'TN: {self.TN}')
            print(f'FN: {self.FN}')
        print(f'Precision: {self.precision:.2f}')
        print(f'Recall:    {self.recall:.2f}')
        print(f'F1:        {self.f1:.2f}')


# def levenshtein(s1: str, s2: str) -> int:
#     '''
#     Levenshtein edit distance, from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
#     '''

#     if len(s1) == len(s2) and s1 == s2:
#         return 0

#     # if len(s1) < len(s2):
#     #     return levenshtein(s2, s1)

#     # # len(s1) >= len(s2)

#     # if not s2:
#     #     return len(s1)

#     # previous_row = range(len(s2) + 1)
#     # for i, c1 in enumerate(s1):
#     #     current_row = [i + 1]
#     #     for j, c2 in enumerate(s2):
#     #         # j+1 instead of j since previous_row and current_row are one character longer
#     #         insertions = previous_row[j + 1] + 1
#     #         deletions = current_row[j] + 1       # than s2
#     #         substitutions = previous_row[j] + (c1 != c2)
#     #         current_row.append(min(insertions, deletions, substitutions))
#     #     previous_row = current_row

#     # return previous_row[-1]

#     return fast_levenshtein.distance(s1, s2)  # pylint: disable=no-member


def evaluate_algorithm(
        algorithm: Algorithm,
        sentenceset1: List[str],
        sentenceset2: List[str],
        alignment: Dict[Tuple[int, int], int]) -> Tuple[int, int, int, int]:
    '''
    Calculates TP, FP, TN, FN for an alignment algorithm.
    '''

    predicted = {k: 0 for k in alignment}

    TP, FP, TN, FN = 0, 0, 0, 0

    for k in algorithm(sentenceset1, sentenceset2):
        predicted[k] = 1

    for k in predicted:
        if k not in alignment:
            raise Exception(
                f'Algorithm produced alignment {k} not found in gold alignment.')

        # check if it was a true positive, true negative, false positive, or false negative.

        if predicted[k] == 1 and alignment[k] == 1:
            # true positive
            TP += 1
        elif predicted[k] == 1 and alignment[k] == 0:
            # false positive
            FP += 1
            print(f'{algorithm.__name__} incorrectly aligned these sentences.')
            print(sentenceset1[k[0]])
            print(sentenceset2[k[1]])
            print()
        elif predicted[k] == 0 and alignment[k] == 0:
            # true negative
            TN += 1
        elif predicted[k] == 0 and alignment[k] == 1:
            # false negative
            FN += 1
            print(f'{algorithm.__name__} incorrectly didn\'t align these sentences.')
            print(sentenceset1[k[0]])
            print(sentenceset2[k[1]])
            print()
        else:
            print('Error:', k, predicted[k], alignment[k])

    return (TP, FP, TN, FN)


def parse_aligned_name(name: str) -> Tuple[str, int, int]:
    '''
    1701.01370-v1-v2 -> (1701.01370, 1, 2)
    cond-mat-0407626-v1-v2 -> (cond-mat-0407626, 1, 2)
    '''

    *namelist, v1, v2 = name.split('-')

    name = '-'.join(namelist)

    return name, int(v1[1]), int(v2[1])


def main():
    '''
    Evaluates success of alignment algorithms based on manually aligned datasets
    '''

    pwd = pathlib.Path(__file__).parent
    alignmentsdir = os.path.join(pwd, 'data', 'alignments')

    algorithms = [align.mass_align, align.lcs_align]
    evaluations = [Evaluation(a) for a in algorithms]

    finalpositive = 0
    finalnegative = 0

    for foldername in os.listdir(alignmentsdir):
        arxivid, v1, v2 = parse_aligned_name(foldername)

        folderpath = os.path.join(alignmentsdir, foldername)

        for sectionfile in os.listdir(folderpath):
            filepath = os.path.join(folderpath, sectionfile)

            with open(filepath, 'r') as file:
                lines = file.read().splitlines()

            section1, section2 = lines[1].split(' | ')

            # I will now get the gold alignment
            alignment = {}
            for line in lines[2:]:
                i1, i2, value = line[1:-1].split(', ')
                i1 = int(i1)
                i2 = int(i2)
                value = int(value)
                alignment[(i1, i2)] = value

            # Now I have the paper id, the versions, and the sections.
            # I will retrieve the sections from the tmp data folder

            v1filename = os.path.join(
                data.SENTENCES_DIR, f'{arxivid}-v{v1}.json')
            v2filename = os.path.join(
                data.SENTENCES_DIR, f'{arxivid}-v{v2}.json')

            with open(v1filename, 'r') as file:
                v1sentences = json.load(file)

            with open(v2filename, 'r') as file:
                v2sentences = json.load(file)

            for section in v1sentences:
                if section[0] == section1:
                    v1sentences = section[1]
                    break

            if not v1sentences:
                raise Exception(
                    f'Did not find section {section1} in {v1filename}')

            for section in v2sentences:
                if section[0] == section2:
                    v2sentences = section[1]
                    break

            if not v2sentences:
                raise Exception(
                    f'Did not find section {section2} in {v2filename}')

            # I now have two lists of sentences.
            # I need to test the alignment algorithm.
            for e in evaluations:
                print(f'--- {section1}, {v1filename} ---')
                results = evaluate_algorithm(
                    e.algorithm, v1sentences, v2sentences, alignment)
                e.add_results(*results)
                finalpositive += (results[0] + results[3])
                finalnegative += (results[1] + results[2])

        print(f'{arxivid} evaluated.')
        for e in evaluations:
            e.display()
        print()

    print()
    print("Final Results:")
    for e in evaluations:
        e.display(verbose=True)

    finalnegative /= len(algorithms)
    finalpositive /= len(algorithms)

    print(f'Positive targets: {finalpositive}')
    print(f'Negative targets: {finalnegative}')


if __name__ == '__main__':
    main()

    # s1 = 'Resummation is essential for a realistic and reliable  calculation of the noun dependence in the region of small and intermediate  values of noun, where the cross section is greatest.'
    # s2 = 'When noun is smaller than noun, we calculate the event rate using the small-noun asymptotic approximation noun and noun phase space.'

    # print(levenshtein(s1, s2))

    # print((len(s1) + len(s2))/2)
