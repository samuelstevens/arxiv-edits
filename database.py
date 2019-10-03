import sqlite3

DB_FILE_NAME = 'data/arxiv-edits.db'


def connection():
    return sqlite3.connect(DB_FILE_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
