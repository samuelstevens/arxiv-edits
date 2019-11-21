'''
Going through all of the sentence pair files in data/sentences, look for sentences that are not identical and categorize them into typos (edit distance < 3), edits (edit distance < 50%), and mistakes (edit distance > 50%).
'''

import csv
import os

from nlp import ArxivTokenizer

TOKENIZER = ArxivTokenizer()


def levenshtein(s1: str, s2: str) -> int:
    '''
    Levenshtein edit distance, from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    '''
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if not s2:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def main():
    '''
    Going through all of the sentence pair files in data/sentences, look for sentences that are not identical and categorize them into typos (edit distance < 3), edits (edit distance < 50%), and mistakes (edit distance > 50%).
    '''

    sentencesdirectory = os.path.join('data', 'sentences')

    paircount = 0
    typocount = 0
    editcount = 0
    mistakecount = 0

    for file in os.listdir(sentencesdirectory):
        filepath = os.path.join(sentencesdirectory, file)

        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for s1, s2 in reader:
                paircount += 1
                avglength = (len(s1) + len(s2)) / 2
                if s1 == s2:
                    continue

                editdistance = levenshtein(s1, s2)

                if editdistance == 0:
                    continue
                elif editdistance < 3:
                    # print('Typo')
                    typocount += 1
                elif editdistance < avglength:
                    # print('Edit found!')
                    editcount += 1
                    # print(s1)
                    # print(s2)
                else:
                    # print('Wrong classification')
                    # print(s1)
                    # print(s2)
                    # print()
                    mistakecount += 1

    print(f'''
Edit:    {editcount:3}
Typo:    {typocount:3}
Mistake: {mistakecount:3}''')


if __name__ == '__main__':
    main()
