"""
Pipeline to run all data collection and cleaning.
"""

import logging

from arxivedits import versions, source, tex, tokenizer, alignment


def pipeline() -> None:
    logging.basicConfig(level=logging.INFO)  # see all logging

    # record a list of all arxiv documents
    if False:
        versions.main()

    # download all files
    if False:
        source.download_all()

    # extract into .tex files
    source.extract_all(again=True)

    # detex all files
    tex.detex_all(again=True)

    # split all files into sentences
    tokenizer.split_all(again=True)

    # do machine alignments (easy alignments)

    ########################################
    # NOTE: This step is very inefficient.
    # Very, very slow. However, it skips
    # documents that do not pass the filter.
    ########################################
    if False:
        alignment.write_machine_alignments()


if __name__ == "__main__":
    pipeline()
