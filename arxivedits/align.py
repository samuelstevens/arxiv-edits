'''
Tries to align the sentences in two versions of a plain text research paper.
'''

import os
import json
import heapq
from typing import List, Tuple, Optional
from collections import namedtuple

from lcs import similarity as sim
from nlp import ArxivTokenizer
from tex import detex

TOKENIZER = ArxivTokenizer()

MISMATCH_PENALTY = 0.1
SKIP_PENALTY = 0

Alignment = namedtuple('Alignment', ['score', 'pairs'])


def align_sentences(s1: List[str], s2: List[str], mismatch: float, skip: float) -> List[Tuple[str, str]]:
    '''
    Aligns lists of sentences via a dynamic programming algorithm first described by Regina Barzilay and Noemie Elhadad in Sentence Alignment for Monolingual Comparable Corpora (2003).
    '''

    if not s1 or not s2:
        return []

    weighttable: List[List[Optional[Alignment]]] = [
        [None for y in range(len(s2))] for x in range(len(s1))]

    for i in range(len(s1)):
        for j in range(len(s2)):

            options: List[Alignment] = []

            if i == 0 and j == 0:
                # first element, always aligned
                option = Alignment(
                    sim(s1[i], s2[j]) - mismatch, [(s1[i], s2[j])]
                )
                options.append(option)

            if j >= 1:
                # s(i,j-1) - skip
                option = Alignment(
                    weighttable[i][j-1].score - skip,
                    weighttable[i][j-1].pairs + [(s1[i], s2[j])]
                )
                options.append(option)

            if i >= 1:
                # s(i-1,j) - skip
                option = Alignment(
                    weighttable[i-1][j].score - skip,
                    weighttable[i-1][j].pairs + [(s1[i], s2[j])]
                )
                options.append(option)

            if i >= 1 and j >= 1:
                # s(i-1,j-1) + sim(i,j)
                option = Alignment(
                    weighttable[i-1][j-1].score + sim(s1[i], s2[j]) - mismatch,
                    weighttable[i-1][j-1].pairs + [(s1[i], s2[j])]
                )
                options.append(option)

                if j >= 2:
                    # s(i-1,j-2) + sim(i,j) + sim(i,j-1)
                    option = Alignment(
                        weighttable[i-1][j-2].score +
                        sim(s1[i], s2[j]) - mismatch +
                        sim(s1[i], s2[j-1]) - mismatch,

                        weighttable[i-1][j-2].pairs + [(s1[i], s2[j])]
                    )
                    options.append(option)

                if i >= 2:
                    # s(i-2,j-1) + sim(i,j) + sim(i-1,j)
                    option = Alignment(
                        weighttable[i-2][j-1].score +
                        sim(s1[i], s2[j]) - mismatch +
                        sim(s1[i-1], s2[j]) - mismatch,

                        weighttable[i-2][j-1].pairs + [(s1[i], s2[j])]
                    )
                    options.append(option)

                if j >= 2 and i >= 2:  # not the most efficient code
                    # s(i-2,j-2) + sim(i,j-1) + sim(i-1,j)
                    option = Alignment(
                        weighttable[i-2][j-2].score +
                        sim(s1[i], s2[j-1]) - mismatch +
                        sim(s1[i-1], s2[j]) - mismatch,

                        weighttable[i-2][j-2].pairs + [(s1[i], s2[j])]
                    )
                    options.append(option)

            bestoption = max(options, key=lambda o: o.score)

            weighttable[i][j] = bestoption

    return weighttable[-1][-1].pairs


def get_sentence_pairs(v1filepath, v2filepath) -> List[Tuple[str, str]]:
    '''
    Returns all the sentence pairs between filepath1 and filepath2. First aligns by sections (title, abstract, introduction, section, subsection). Then aligns using weighted-LCS.

    TODO: find better parameter names
    '''

    with open(v1filepath, 'r') as fin:
        v1source = json.load(fin)

    with open(v2filepath, 'r') as fin:
        v2source = json.load(fin)

    # Because these section titles should be very similar, I am going to use a greedy approach and apply weighted-lcs to all possible pairs of section titles. Then I will take the maximum from those pairs and align those sections

    sortedpairs = []

    for v1section in v1source:
        for v2section in v2source:
            _, v1title, v1content = v1section
            _, v2title, v2content = v2section

            score = sim(v1title, v2title)
            possiblesectionpair = (score, (v1content, v2content),
                                   (v1title, v2title))
            sortedpairs.append(possiblesectionpair)

    # assumes that each version has the same number of sections (len(v1source))
    matchedsections = heapq.nlargest(len(v1source), sortedpairs)

    sentencepairs = []

    for _, contentpair, _ in matchedsections:
        text1 = detex(contentpair[0])
        text2 = detex(contentpair[1])
        print(text1)
        print(text2)

        # TODO: WORKING HERE

        sentences1 = TOKENIZER.split(text1, group='sentence')
        sentences2 = TOKENIZER.split(text2, group='sentence')
        sentencepairs.extend(align_sentences(
            sentences1, sentences2, MISMATCH_PENALTY, SKIP_PENALTY))

    return sentencepairs


def main():
    '''
    For every file in data/sections, find its other versions. Then create sentence pairs and write them to data/pairs.
    '''

    textfiles = os.path.join('data', 'sections')
    sentencedirectory = os.path.join('data', 'sentences')

    already_seen = set([])

    if not os.path.isdir(sentencedirectory):
        os.mkdir(sentencedirectory)

    for file in os.listdir(textfiles):
        filename, extension = os.path.splitext(file)
        arxiv_id, version_code = filename.split('-')

        if arxiv_id in already_seen:
            continue

        # assume there are no double digit versions
        version = int(version_code[-1])

        # next version is something like 0704.0002-v2
        nextversionfilepath = os.path.join(
            textfiles, f'{arxiv_id}-v{version + 1}' + extension)

        # keep looking for the next version of the paper
        while os.path.isfile(nextversionfilepath):

            # initial version is something like 0704.0002-v1
            currentversionfilepath = os.path.join(
                textfiles, f'{arxiv_id}-v{version}' + extension)

            sentencepairs = get_sentence_pairs(
                currentversionfilepath, nextversionfilepath)

            # include both versions in the file name
            sentencefilepath = os.path.join(
                sentencedirectory, f'{arxiv_id}-v{version}-v{version+1}')

            with open(sentencefilepath, 'w') as file:
                # write every sentence pair "sentence", "sentence"
                # TODO: think about escaping " inside the sentences.
                for (sentence1, sentence2) in sentencepairs:
                    file.write(f'"{sentence1}", "{sentence2}"')

            version += 1

            nextversionfilepath = os.path.join(
                textfiles, f'{arxiv_id}-v{version + 1}' + extension)

        # only look at an id once
        already_seen.add(arxiv_id)
        return


if __name__ == '__main__':
    main()

    # sentences1 = [
    #     'An additional complication arises when the fragmentation radiation is assumed to be exactly collinear to the photon\'s momentum, as implied by the photon fragmentation functions noun.',
    #     'The collinear approximation constrains from below the values of noun accessible to noun: noun verbs noun.',
    #     'The size of the fragmentation contribution may depend strongly on the values of noun and noun as a consequence of rapid variation of noun with noun.'
    # ]

    # sentences2 = [
    #     'An additional complication arises when the fragmentation radiation is assumed to be exactly collinear to the photon\'s momentum, as implied by the photon fragmentation functions noun.',
    #     'The collinear approximation constrains from below the values of noun accessible to noun: noun verbs noun.',
    #     'The size of the fragmentation contribution may depend strongly on the values of noun and noun as a consequence of rapid variation of noun with noun.']

    # print(align_sentences(sentences1, sentences2, 0.1, 0.1))
