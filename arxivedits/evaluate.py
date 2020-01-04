'''
'''

import csv
import os
import pathlib
import json
from typing import Tuple, Callable, List, Dict

import Levenshtein as fast_levenshtein
import data
import align


def levenshtein(s1: str, s2: str) -> int:
    '''
    Levenshtein edit distance, from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    '''

    if len(s1) == len(s2) and s1 == s2:
        return 0

    # if len(s1) < len(s2):
    #     return levenshtein(s2, s1)

    # # len(s1) >= len(s2)

    # if not s2:
    #     return len(s1)

    # previous_row = range(len(s2) + 1)
    # for i, c1 in enumerate(s1):
    #     current_row = [i + 1]
    #     for j, c2 in enumerate(s2):
    #         # j+1 instead of j since previous_row and current_row are one character longer
    #         insertions = previous_row[j + 1] + 1
    #         deletions = current_row[j] + 1       # than s2
    #         substitutions = previous_row[j] + (c1 != c2)
    #         current_row.append(min(insertions, deletions, substitutions))
    #     previous_row = current_row

    # return previous_row[-1]

    return fast_levenshtein.distance(s1, s2)  # pylint: disable=no-member


def evaluate_algorithm(
        algorithm: Callable[[List[str], List[str]], List[Tuple[int, int]]],
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
        elif predicted[k] == 0 and alignment[k] == 0:
            # true negative
            TN += 1
        elif predicted[k] == 0 and alignment[k] == 1:
            # false negative
            FN += 1
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
    TP, FP, TN, FN = 0, 0, 0, 0
    for filename in os.listdir(alignmentsdir):

        name, _ = os.path.splitext(filename)

        arxivid, v1, v2 = parse_aligned_name(name)

        filepath = os.path.join(alignmentsdir, filename)

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

        v1filename = os.path.join(data.SENTENCES_DIR, f'{arxivid}-v{v1}.json')
        v2filename = os.path.join(data.SENTENCES_DIR, f'{arxivid}-v{v2}.json')

        with open(v1filename, 'r') as file:
            v1 = json.load(file)

        with open(v2filename, 'r') as file:
            v2 = json.load(file)

        for section in v1:
            if section[0] == section1:
                v1sentences = section[1]
                break

        if not v1sentences:
            raise Exception(f'Did not find section {section1} in {v1filename}')

        for section in v2:
            if section[0] == section2:
                v2sentences = section[1]
                break

        if not v2sentences:
            raise Exception(f'Did not find section {section2} in {v2filename}')

        # I now have two lists of sentences.
        # I need to test the alignment algorithm.
        _TP, _FP, _TN, _FN = evaluate_algorithm(align.lcs_align, v1sentences,
                                                v2sentences, alignment)
        TP += _TP
        FP += _FP
        TN += _TN
        FN += _FN

    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    f1 = 2 * (precision * recall) / (precision + recall)
    print(precision, recall, f1)


def demo():
    '''
    Going through all of the sentence pair files in data/sentences, look for sentences that are not identical and categorize them into typos (edit distance < 3), edits (edit distance < 50 %), and mistakes (edit distance > 50%).
    '''

    paircount = 0
    typocount = 0
    editcount = 0
    mistakecount = 0

    outputfile = open('data/examples.txt', 'w')

    for file in os.listdir(data.SENTENCES_DIR):
        filepath = os.path.join(data.SENTENCES_DIR, file)

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for s1, s2 in reader:
                paircount += 1
                avglength = (len(s1) + len(s2)) / 2
                if s1 == s2:
                    continue

                editdistance = levenshtein(s1, s2)

                if editdistance == 0:
                    print('Oops')
                    continue
                elif editdistance < 3:
                    typocount += 1
                    outputfile.write('TYPO: \n')
                    outputfile.write(s1 + '\n')
                    outputfile.write(s2 + '\n')
                elif editdistance < avglength * 3/4:
                    editcount += 1
                    outputfile.write('EDIT: \n')
                    outputfile.write(s1 + '\n')
                    outputfile.write(s2 + '\n')
                else:
                    mistakecount += 1
                    outputfile.write('MISTAKE: \n')
                    outputfile.write(s1 + '\n')
                    outputfile.write(s2 + '\n')
                outputfile.write(str(editdistance) + '/' +
                                 str(avglength) + '\n')
                outputfile.write('\n')

    outputfile.flush()
    outputfile.close()

    print(f'''


Edit:    {editcount: 3}
Typo:    {typocount: 3}
Mistake: {mistakecount: 3}''')


if __name__ == '__main__':
    main()

    # s1 = 'Resummation is essential for a realistic and reliable  calculation of the noun dependence in the region of small and intermediate  values of noun, where the cross section is greatest.'
    # s2 = 'When noun is smaller than noun, we calculate the event rate using the small-noun asymptotic approximation noun and noun phase space.'

    # print(levenshtein(s1, s2))

    # print((len(s1) + len(s2))/2)
