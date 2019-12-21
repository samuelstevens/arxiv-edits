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
EXTRACTED_DIR = os.path.join(DATA_DIR, 'unzipped')
SECTIONS_DIR = os.path.join(DATA_DIR, 'sections')
SENTENCES_DIR = os.path.join(DATA_DIR, 'sentences')
UNZIPPED_DIR = os.path.join(DATA_DIR, 'unzipped')
TEXT_DIR = os.path.join(DATA_DIR, 'text')


def connection():
    '''
    Creates and returns a new connection to a persistent database
    '''
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
