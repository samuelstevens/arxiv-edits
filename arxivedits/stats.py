'''
Generates stats for arXiv as a data source.

* Might want to take a random sample of papers with 2+ versions, and a sample of all papers.
* From the random sample, write the arxiv ids to a text file
* From the text file, scrape all the papers + versions.
* From the text file and for all downloaded papers, measure the statistics (listed in notebook)
'''
import os

import data


def get_random_sample(samplesize=1000, multipleversions=False):
    '''
    Takes a random sample of all rows.
    '''

    con = data.connection()

    if multipleversions:
        query = 'SELECT * FROM papers WHERE version_count > 2 ORDER BY RANDOM() LIMIT ?'
    else:
        query = 'SELECT * FROM papers ORDER BY RANDOM() LIMIT ?'

    return con.execute(query, (samplesize,)).fetchall()


def main():
    '''
    Takes a random sample and writes them to a text file. Then calculates stats.
    '''

    multipleversions = True

    extension = '-only-multiversion' if multipleversions else '-all'

    samplefilepath = os.path.join(data.DATA_DIR, f'sample{extension}.txt')

    # generate random sample if it doesn't exist
    if not os.path.isfile(samplefilepath):
        sample = get_random_sample(multipleversions=multipleversions)

        with open(samplefilepath, 'w') as file:
            for row in sample:
                file.write(f'{row[0]}\n')

    with open(samplefilepath, 'r') as file:
        ids = file.read().split()

    print(f'{len(ids)} ids in sample.')

    for arxivid in ids:
        sourcefilepath = os.path.join(data.SOURCE_DIR, arxivid)

        if not os.path.isfile(sourcefilepath):
            # download source file.
            pass


if __name__ == '__main__':
    main()
