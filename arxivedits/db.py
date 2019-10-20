import sqlite3

DB_FILE_NAME = 'data/arxiv-edits.db'


IDF_DB = 'data/idf'
TEX_DB = 'data/tex'


def connection():
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
