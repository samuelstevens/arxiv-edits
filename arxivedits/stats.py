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


import data
import source

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

    return sample


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

    source.extract_all()


if __name__ == '__main__':
    main()
