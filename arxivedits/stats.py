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
from typing import List, Tuple, Dict

import Levenshtein

import data
import source
import tex
import sections
import tokenizer
from structures import Section, Sentence


MULTIPLE_VERSIONS = True
SENTENCELENGTH = 20


def get_random_sample(samplesize=1000, multipleversions=MULTIPLE_VERSIONS):
    '''
    Gets a new random sample unless one exists.
    '''

    extension = '-only-multiversion' if multipleversions else '-all'

    samplefilepath = os.path.join(data.DATA_DIR, f'sample{extension}.csv')

    if os.path.isfile(samplefilepath):
        with open(samplefilepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            ids = [(arxivid, int(versioncount))
                   for arxivid, versioncount in reader]
        return ids

    con = data.connection()

    if multipleversions:
        query = 'SELECT * FROM papers WHERE version_count > 1 ORDER BY RANDOM() LIMIT ?'
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
                        sentence for sentence in sentencelist if len(sentence) > SENTENCELENGTH]

                    sentences.extend(sentencelist)

    print(f'{len(sentences)} sentences in {len(sectionedsample)} extracted documents: {len(sentences) / len(sectionedsample):.1f} per extracted document.')

    print(f'{len(sentences)} sentences in {len(sample)} documents: {len(sentences) / len(sample):.1f} per (extracted) document.')

    embeddedoldlatexpattern = re.compile(r'\$.*\$')
    embeddedcurrentlatexpatern = re.compile(r'\\\(.*\\\)')

    nonmathsentences = [
        s for s in sentences if not embeddedoldlatexpattern.search(s)]

    nonmathsentences = [
        s for s in nonmathsentences if not embeddedcurrentlatexpatern.search(s)]

    print(f'{len(nonmathsentences)} sentences (with no math) in {len(sectionedsample)} extracted documents: {len(nonmathsentences) / len(sectionedsample):.1f} per extracted document.')
    print(f'{len(nonmathsentences)} sentences (with no math) in {len(sample)} documents: {len(nonmathsentences) / len(sample):.1f} per document.')

    print(f'{(len(sentences) - len(nonmathsentences)) / len(sentences) * 100:.1f}% have embedded LaTeX math.')


def manually_align(arxivid, versionpair):
    '''
    Function to help manually align a paper.
    '''

    arxividpath = arxivid.replace('/', '-')

    v1 = f'{arxividpath}-v{versionpair[0]}.json'
    v2 = f'{arxividpath}-v{versionpair[1]}.json'

    v1filename = os.path.join(data.SENTENCES_DIR, v1)

    if not os.path.isfile(v1filename):
        return

    with open(v1filename, 'r') as jsonfile:
        v1: List[Section] = json.load(jsonfile)

    with open(os.path.join(data.SENTENCES_DIR, v2), 'r') as jsonfile:
        v2: List[Section] = json.load(jsonfile)

    alignedsections = sections.align(v1, v2)

    foldername = os.path.join(
        data.ALIGNMENTS_DIR, f'{arxividpath}-v{versionpair[0]}-v{versionpair[1]}', 'working-set')

    os.makedirs(foldername, exist_ok=True)

    interestingjoins = 0
    boringjoins = 0

    for score, titles, contents in alignedsections:
        v1sentences, v2sentences = contents
        v1title, v2title = titles

        pairlistfilename = os.path.join(foldername, f'{v1title}-TODO.txt')

        remainingfilename = os.path.join(
            foldername, f'{v1title}-REMAINING.txt')

        v1sentenceset = {s: i for i, s in enumerate(v1sentences)}
        v2sentenceset = {s: i for i, s in enumerate(v2sentences)}

        pairlist: Dict[Tuple[Sentence, Sentence], int] = {}

        for i, s1 in enumerate(v1sentences):
            for j, s2 in enumerate(v2sentences):

                pairlist[(i, j)] = 0
                if s1 not in v1sentenceset or s2 not in v2sentenceset:
                    continue

                score = Levenshtein.distance(s1, s2)

                if score == 0:
                    # print('Identical')
                    boringjoins += 1
                    del v1sentenceset[s1]
                    del v2sentenceset[s2]
                    pairlist[(i, j)] = 1
                elif score / max(len(s1), len(s2)) < 0.2:
                    interestingjoins += 1
                    # print('Typo')
                    # del v1sentenceset[s1]
                    # del v2sentenceset[s2]
                    # pairlist[(i, j)] = 1

        with open(pairlistfilename, 'w') as file:
            file.write('Pairs\n')
            file.write(f'{v1title} | {v2title}\n')
            file.writelines(
                [f'({pair[0]}, {pair[1]}, {pairlist[pair]})\n' for pair in sorted(pairlist)])

        with open(remainingfilename, 'w') as file:
            file.write('Remaining\n')
            file.write(
                'Instructions: open the relevant data files and look through any sentences listed in this file. Find them and their matching sentence, and edit the relevant alignment.txt file.\n')
            file.write(f'{v1title} | {v2title}\n')
            file.write('---v1---\n')
            file.writelines(
                [f'{v1sentenceset[s]}: \t{s}\n' for s in v1sentenceset])
            file.write('---v2---\n')
            file.writelines(
                [f'{v2sentenceset[s]}: \t{s}\n' for s in v2sentenceset])
            file.write('\n')

    # print(f"manually_align('{arxivid}', {versionpair}) # {interestingjoins}")
    print(f'{arxivid} {versionpair}: \t{boringjoins / (boringjoins + interestingjoins):.2f}')


def main():
    '''
    Takes a random sample and writes them to a text file. Then calculates stats.
    '''

    sample = get_random_sample(multipleversions=True)

    # takes a smaller sample
    sample = sample[:200]

    print(f'{len(sample)} ids in sample.')

    downloadcount = len(sample)

    for arxivid, versioncount in sample:
        if source.is_downloaded(arxivid, versioncount):
            downloadcount -= 1

    print(f'{downloadcount} to download. Estimated {downloadcount * 2 * 30 / 60 / 60:.1f} hours ({downloadcount * 2 * 30 / 60 :.0f} minutes).')

    for arxivid, versioncount in sample:
        source.download_source_files(arxivid, versioncount)

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
    stats(sample)

    # for arxivid, versioncount in sample:
    #     for i in range(versioncount - 1):
    #         manually_align(arxivid, (i, i + 1))

    # manually_align('1701.01370', (1, 2))  # 124
    # manually_align('1807.05692', (2, 3))  # 0
    # manually_align('1307.1155', (1, 2))  # 14
    # manually_align('1201.2485', (1, 2))  # 24
    # manually_align('1306.3888', (1, 2))  # 87
    # manually_align('1306.3888', (2, 3))  # 89
    # manually_align('cond-mat/0407626', (1, 2))  # 56
    # manually_align('1208.2382', (1, 2))  # 4
    # manually_align('1701.01370', (1, 2))  # 124
    # manually_align('1807.05692', (2, 3))  # 0


if __name__ == '__main__':
    main()
