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


import data
import source
import tex
import sections
import tokenizer

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


def main():
    '''
    Takes a random sample and writes them to a text file. Then calculates stats.
    '''

    sample = get_random_sample()

    # modifies to smaller sample
    sample = sample[:50]

    print(f'{len(sample)} ids in sample.')

    downloadcount = len(sample)

    for arxivid, versioncount in sample:
        if source.is_downloaded(arxivid, versioncount):
            downloadcount -= 1

    print(f'{downloadcount} to download. Estimated {downloadcount * 2 * 30 / 60 / 60:.1f} hours.')

    for arxivid, versioncount in sample:
        source.download_source_files(arxivid, versioncount)

    # source.extract_all()
    # tex.main()
    # sections.main()
    # tokenizer.main()

    print(f'Given {len(sample)} documents:')

    # * total # of papers
    # * total #, % of papers with 2+ versions
    # * total # of revision pairs: (1, 2), (2, 3), etc
    # * total # of sentences
    # * % of sentences with embedded LaTeX
    # * % of sentences deleted
    # * % of sentences modified (>= 4 in distance)
    # * % of sentences with typos (< 4 in distance)

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


if __name__ == '__main__':
    main()
