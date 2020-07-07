"""
Pipeline to run all data collection and cleaning.
"""

import logging

from arxivedits import versions, source, tex, tokenizer


def pipeline() -> None:
    logging.basicConfig(level=logging.INFO)  # see all logging

    # record a list of all arxiv documents
    if False:
        versions.main()

    # download all files
    if True:
        source.download_all()

    # extract into .tex files
    if False:
        source.extract_all(again=True)

    # detex all files
    if False:
        tex.detex_all(again=True)

    # split all files into sentences
    if False:
        tokenizer.split_all(again=True)

    # do machine alignments (easy alignments)
    if False:
        pass


if __name__ == "__main__":
    pipeline()
