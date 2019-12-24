'''
Provides a central location to store all data locations
'''

import sqlite3
import os

DB_FILE_NAME = 'data/arxivedits.sqlite3'
IDF_DB = 'data/idf'
TEX_DB = 'data/tex'

DATA_DIR = 'data'

SOURCE_DIR = os.path.join(DATA_DIR, 'source')
SECTIONS_DIR = os.path.join(DATA_DIR, 'sections')
SENTENCES_DIR = os.path.join(DATA_DIR, 'sentences')
UNZIPPED_DIR = os.path.join(DATA_DIR, 'unzipped')
TEXT_DIR = os.path.join(DATA_DIR, 'text')
ALIGNMENTS_DIR = os.path.join(DATA_DIR, 'alignments')


def connection():
    '''
    Creates and returns a new connection to a persistent database
    '''
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)


def is_x(arxivid, versioncount, directory, extension='') -> bool:
    '''
    Checks if all versions of an arxiv id are in a directory. Useful to see what % were successfully 'detexed' or extracted.
    '''
    arxividpath = arxivid.replace('/', '-')

    for i in range(versioncount):
        filepath = os.path.join(
            directory, f'{arxividpath}-v{i + 1}{extension}')
        if not os.path.isfile(filepath):
            return False

    return True
