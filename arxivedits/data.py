'''
Provides a central location to store all data locations
'''

import sqlite3
import os


DATA_DIR = 'data'

SOURCE_DIR = os.path.join(DATA_DIR, 'source')
SECTIONS_DIR = os.path.join(DATA_DIR, 'sections')
SENTENCES_DIR = os.path.join(DATA_DIR, 'sentences')
UNZIPPED_DIR = os.path.join(DATA_DIR, 'unzipped')
TEXT_DIR = os.path.join(DATA_DIR, 'text')
ALIGNMENTS_DIR = os.path.join(DATA_DIR, 'alignments')

DB_FILE_NAME = os.path.join(DATA_DIR, 'arxivedits.sqlite3')
IDF_DB = os.path.join(DATA_DIR, 'idf')

# if not os.path.isdir(DATA_DIR):
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(SECTIONS_DIR, exist_ok=True)
os.makedirs(SENTENCES_DIR, exist_ok=True)
os.makedirs(UNZIPPED_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(ALIGNMENTS_DIR, exist_ok=True)


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
