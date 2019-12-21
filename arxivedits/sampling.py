'''
Needs to take a random sample of the database.

* Might want to take a random sample of papers with 2+ versions, and a sample of all papers.
* From the random sample, write the arxiv ids to a text file
* From the text file, scrape all the papers + versions.
* From the text file and for all downloaded papers, measure the statistics (listed in notebook)
'''

import db


def get_random_sample(samplesize=1000, multipleversions=False):
    '''
    Takes a random sample of all rows.
    '''

    con = db.connection()

    if multipleversions:
        query = 'SELECT * FROM papers WHERE version_count > 2 ORDER BY RANDOM() LIMIT ?'
    else:
        query = 'SELECT * FROM papers ORDER BY RANDOM() LIMIT ?'

    return con.execute(query, (samplesize,)).fetchall()


def main():
    '''
    Takes a random sample and writes them to a text file.
    '''

    sample = get_random_sample(multipleversions=True)

    with open('data/sample.txt', 'w') as file:
        for row in sample:
            file.write(f'{row[0]}\n')


if __name__ == '__main__':
    main()
