"""
Runs every step in the pipeline (incomplete)
"""

import tex
import source
import tokenizer


def main():
    """
    Runs every step in the pipeline (incomplete)
    """
    source.main()
    tex.main()
    tokenizer.main()  # data/text -> data/sections


if __name__ == "__main__":
    main()
