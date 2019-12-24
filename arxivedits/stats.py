'''
Generates stats for arXiv as a data source.

* Might want to take a random sample of papers with 2+ versions, and a sample of all papers.
* From the random sample, write the arxiv ids to a text file
* From the text file, scrape all the papers + versions.
* From the text file and for all downloaded papers, measure the following statistics
    * total # of papers
    * total #, % of papers with 2+ versions
    * total # of revision pairs: (1, 2), (2, 3), etc
    * % of sentences with embedded LaTeX
    * % of sentences deleted
    * % of sentences modified (>= 4 in distance)
    * % of sentences with typos (< 4 in distance)
'''
import os
import csv
import json
import re
import heapq
from typing import List, Tuple, Dict
from collections import Counter


import data
import source
import tex
import sections
import tokenizer
import evaluate
from structures import Section, Sentence


MULTIPLE_VERSIONS = True


def get_random_sample(samplesize=1000, multipleversions=False):
    '''
    Gets a new random sample unless one exists.
    '''

    extension = '-only-multiversion' if MULTIPLE_VERSIONS else '-all'

    samplefilepath = os.path.join(data.DATA_DIR, f'sample{extension}.csv')

    if os.path.isfile(samplefilepath):
        with open(samplefilepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            ids = [(arxivid, int(versioncount))
                   for arxivid, versioncount in reader]
        return ids

    con = data.connection()

    if multipleversions:
        query = 'SELECT * FROM papers WHERE version_count > 2 ORDER BY RANDOM() LIMIT ?'
    else:
        query = 'SELECT * FROM papers ORDER BY RANDOM() LIMIT ?'

    sample = con.execute(query, (samplesize,)).fetchall()

    with open(samplefilepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(sample)

    return [(arxivid, versioncount) for arxivid, versioncount in sample]


def stats(sample: List[Tuple[str, int]]):
    '''
    Calculates some stats for some given ids
    '''

    print(f'Given {len(sample)} documents:')

    extractedsample = [(arxivid, versioncount) for arxivid,
                       versioncount in sample if source.is_extracted(arxivid, versioncount)]

    print(f'{len(extractedsample)} documents could be extracted.')

    multipleversioncount = len(
        [_ for _, versioncount in extractedsample if versioncount > 2])

    if not MULTIPLE_VERSIONS:
        print(
            f'{multipleversioncount} ({len(extractedsample) / multipleversioncount:2f}%)have 2+ versions.')

    paircount = 0
    for _, versioncount in extractedsample:
        paircount += versioncount - 1

    print(f'There are {paircount} revision pairs.')

    detexedsample = [(a, v)
                     for a, v in extractedsample if tex.is_detexed(a, v)]

    print(f'{len(detexedsample)} documents could be detexed.')

    sectionedsample = [(a, v)
                       for a, v in detexedsample if sections.is_sectioned(a, v)]

    print(f'{len(sectionedsample)} documents could be sectioned.')

    sentences = []

    for arxivid, versioncount in sectionedsample:
        arxividpath = arxivid.replace('/', '-')

        for i in range(versioncount):
            filepath = os.path.join(
                data.SENTENCES_DIR, f'{arxividpath}-v{i + 1}.json')

            with open(filepath, 'r') as file:
                contents = json.load(file)

            for title, sentencelist in contents:
                if title != '### Initial Section (MANUAL) ###':
                    sentencelist = [
                        sentence for sentence in sentencelist if len(sentence) > 20]

                    sentences.extend(sentencelist)

    print(f'{len(sentences)} sentences in {len(sectionedsample)} documents: {len(sentences) / len(sectionedsample):.1f} per document.')

    embeddedoldlatexpattern = re.compile(r'\$.*\$')
    embeddedcurrentlatexpatern = re.compile(r'\\\(.*\\\)')

    nonmathsentences = [
        s for s in sentences if not embeddedoldlatexpattern.search(s)]

    nonmathsentences = [
        s for s in nonmathsentences if not embeddedcurrentlatexpatern.search(s)]

    print(f'{len(nonmathsentences)} sentences (with no math) in {len(sectionedsample)} documents: {len(nonmathsentences) / len(sectionedsample):.1f} per document.')

    print(f'{(len(sentences) - len(nonmathsentences)) / len(sentences) * 100:.1f}% have embedded LaTeX math.')


def find_pairs(sample: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    '''
    Finds pairs of documents that match particular criteria for later manual evaluation.
    '''
    sectionedsample = [(a, v)
                       for a, v in sample if sections.is_sectioned(a, v)]

    for arxivid, versioncount in sectionedsample:

        arxividpath = arxivid.replace('/', '-')

        for i in range(versioncount - 1):
            versionpair = (i + 1, i + 2)

            v1 = f'{arxividpath}-v{versionpair[0]}.json'
            v2 = f'{arxividpath}-v{versionpair[1]}.json'

            with open(os.path.join(data.SECTIONS_DIR, v1), 'r') as jsonfile:
                v1 = json.load(jsonfile)

            with open(os.path.join(data.SECTIONS_DIR, v2), 'r') as jsonfile:
                v2 = json.load(jsonfile)


def manually_align(arxivid, versionpair):
    '''
    Function to help manually align a paper.
    '''

    arxividpath = arxivid.replace('/', '-')

    v1 = f'{arxividpath}-v{versionpair[0]}.json'
    v2 = f'{arxividpath}-v{versionpair[1]}.json'

    with open(os.path.join(data.SENTENCES_DIR, v1), 'r') as jsonfile:
        v1: List[Section] = json.load(jsonfile)

    with open(os.path.join(data.SENTENCES_DIR, v2), 'r') as jsonfile:
        v2: List[Section] = json.load(jsonfile)

    alignedsections = sections.align(v1, v2)

    # v1sentenceset = [sentence for _, content in v1 for sentence in content]
    # v2sentenceset = [sentence for _, content in v2 for sentence in content]

    pairlistfilename = os.path.join(
        data.ALIGNMENTS_DIR, f'{arxividpath}-v{versionpair[0]}-v{versionpair[1]}.txt')

    remainingfilename = os.path.join(
        data.ALIGNMENTS_DIR, f'{arxividpath}-v{versionpair[0]}-v{versionpair[1]}-REMAINING.txt')

    with open(remainingfilename, 'w') as file:
        file.write('Remaining\n')
        file.write(
            'Instructions: open the relevant data files and look through any sentences listed in this file. Find them and their matching sentence, and edit the relevant alignment.txt file.\n')

    with open(pairlistfilename, 'w') as file:
        file.write('Pairs\n')

    for score, titles, contents in alignedsections:
        v1sentences, v2sentences = contents
        v1title, v2title = titles

        v1sentenceset = {s: i for i, s in enumerate(v1sentences)}
        v2sentenceset = {s: i for i, s in enumerate(v2sentences)}

        pairlist: Dict[Tuple[Sentence, Sentence], int] = {}
        # remainingsentences = (set(), set())

        # for s1 in v1sentences:
        #     for s2 in v2sentences:
        #         score = evaluate.levenshtein(s1, s2)
        #         if score > 0 and score < 100:
        #             print(score)
        #             print(s1)
        #             print(s2)
        #             print(score / min(len(s1), len(s2)))
        #             print()

        for i, s1 in enumerate(v1sentences):
            for j, s2 in enumerate(v2sentences):

                pairlist[(i, j)] = 0
                if s1 not in v1sentenceset or s2 not in v2sentenceset:
                    continue

                score = evaluate.levenshtein(s1, s2)

                if score == 0:
                    # print('Identical')
                    del v1sentenceset[s1]
                    del v2sentenceset[s2]
                    pairlist[(i, j)] = 1
                elif score / max(len(s1), len(s2)) < 0.05:
                    # print('Typo')
                    del v1sentenceset[s1]
                    del v2sentenceset[s2]
                    pairlist[(i, j)] = 1

        with open(pairlistfilename, 'a') as file:
            file.write(f'{v1title} | {v2title}\n')
            file.writelines(
                [f'({pair[0]}, {pair[1]}, {pairlist[pair]})\n' for pair in sorted(pairlist)])

        with open(remainingfilename, 'a') as file:
            file.write(f'{v1title} | {v2title}\n')
            file.write('---v1---\n')
            file.writelines(
                [f'{v1sentenceset[s]}: \t{s}\n' for s in v1sentenceset])
            file.write('---v2---\n')
            file.writelines(
                [f'{v2sentenceset[s]}: \t{s}\n' for s in v2sentenceset])
            file.write('\n')


def main():
    '''
    Takes a random sample and writes them to a text file. Then calculates stats.
    '''

    sample = get_random_sample()

    # takes a smaller sample
    sample = sample[:50]

    print(f'{len(sample)} ids in sample.')

    downloadcount = len(sample)

    for arxivid, versioncount in sample:
        if source.is_downloaded(arxivid, versioncount):
            downloadcount -= 1

    print(f'{downloadcount} to download. Estimated {downloadcount * 2 * 30 / 60 / 60:.1f} hours.')

    for arxivid, versioncount in sample:
        # source.download_source_files(arxivid, versioncount)
        pass

    # source.extract_all()
    # tex.main()
    # sections.main()
    # tokenizer.main()

    # * total # of papers
    # * total #, % of papers with 2+ versions
    # * total # of revision pairs: (1, 2), (2, 3), etc
    # * total # of sentences
    # * % of sentences with embedded LaTeX
    # * % of sentences deleted
    # * % of sentences modified (>= 4 in distance)
    # * % of sentences with typos (< 4 in distance)
    # stats(sample)

    # find_pairs(sample)
    manually_align('1212.5406', (1, 2))
    # manually_align('1212.5406', (2, 3))


if __name__ == '__main__':
    main()
