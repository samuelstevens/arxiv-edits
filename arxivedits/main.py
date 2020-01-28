"""
Runs every step in the pipeline (incomplete)
"""

from tex import main as tex
from idf import main as idf
from align import main as align
from sections import main as sections
from tokenizer import main as tokenize


def main():
    """
    Runs every step in the pipeline (incomplete)
    """
    tex()  # data/unzipped -> data/text
    idf()  # data/text -> data/IDF_DB
    sections()  # data/text -> data/sections
    tokenize()  # data/sections -> data/sentences


if __name__ == "__main__":
    main()
