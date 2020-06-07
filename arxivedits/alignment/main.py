"""
For each document pair, perform the following steps:

1. diff the two documents **(COMPLETE)**
2. create an alignment based on only identical sentences. **(COMPLETE)**
3. perform easy alignments (Chao's code) **(COMPLETE)**
4. add alignments to the stored alignment **(COMPLETE)**
5. get unaligned sentences **(COMPLETE)** (kind of too easy)
6. create a .csv file **(COMPLETE)**
7. manually align
8. merge with old alignments **(COMPLETE)**
9. profit
"""

import os
import logging

from tqdm import tqdm

from arxivedits import util, data, diff

from arxivedits.alignment.align import (
    Alignment,
    easy_align,
    process_easy_align,
    easy_align_outside_doc,
)
from arxivedits.alignment.util import preprocess_single_sent


# ids = tqdm(util.good_id_iter(), total=util.good_id_len)
# ids = util.good_id_iter()
ids = list(util.good_id_iter())[:20]


def write_unaligned():
    logging.info("Creating models and writing unaligned sentences to disk.")

    for arxivid, version1, version2 in tqdm([("hep-th-0607021", 1, 2)]):
        alignment = Alignment(arxivid, version1, version2)
        easy_alignments = easy_align(arxivid, version1, version2)
        process_easy_align(easy_alignments, alignment)

        easy_alignments_outside = easy_align_outside_doc(easy_alignments)
        process_easy_align(easy_alignments_outside, alignment)
        diff._hashable_line_diff.cache_clear()  # clear it after finishing a document

        alignment.write_unaligned_csv()
        alignment.save()


def read_aligned():
    logging.info("Updating models with manual annotations and writing to disk")
    for arxivid, version1, version2 in ids:
        if os.path.isfile(
            data.alignment_finished_path(arxivid, version1, version2)
        ) and os.path.isfile(data.alignment_model_path(arxivid, version1, version2)):
            alignment = Alignment.load(arxivid, version1, version2)

            alignment.read_unaligned_csv()

            alignment.save()


def write_final_aligned():
    logging.info("Writing final annotations to .csv for inspection.")
    for arxivid, version1, version2 in ids:
        if os.path.isfile(
            data.alignment_finished_path(arxivid, version1, version2)
        ) and os.path.isfile(data.alignment_model_path(arxivid, version1, version2)):

            alignment = Alignment.load(arxivid, version1, version2)

            alignment.write_csv()


def test_script():
    for arxivid, version1, version2 in tqdm(data.SAMPLE_IDS):
        alignment = Alignment(arxivid, version1, version2)
        alignment = Alignment.load(arxivid, version1, version2)
        alignment.read_unaligned_csv()
        alignment.write_unaligned_csv()
        # alignment.write_csv()


def start_of_pipeline():
    for arxivid, version1, version2 in tqdm(data.SAMPLE_IDS):
        alignment = Alignment(arxivid, version1, version2)
        easy_alignments = easy_align(arxivid, version1, version2)
        process_easy_align(easy_alignments, alignment)

        easy_alignments_outside = easy_align_outside_doc(easy_alignments)
        process_easy_align(easy_alignments_outside, alignment)
        diff._hashable_line_diff.cache_clear()  # clear it after finishing a document
        alignment.save()


if __name__ == "__main__":
    # write_unaligned()

    test_script()
    # print(preprocess_single_sent.cache_info())
    # print(diff.sent_filter.cache_info())
