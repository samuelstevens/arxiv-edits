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

from tqdm import tqdm

from arxivedits import util, data, diff

from arxivedits.alignment.align import (
    Alignment,
    easy_align,
    process_easy_align,
    similar,
    easy_align_outside_doc,
    preprocess_single_sent,
)

# ids = tqdm(util.good_id_iter(), total=util.good_id_len)
# ids = util.good_id_iter()
ids = tqdm(list(util.good_id_iter())[:20])


def write_unaligned(overwrite=False):
    print("Creating models and writing unaligned sentences to disk.")

    for arxivid, version1, version2 in ids:
        if (
            os.path.isfile(data.alignment_model_path(arxivid, version1, version2))
            and not overwrite
        ):
            alignment = Alignment.load(arxivid, version1, version2)

        else:
            alignment = Alignment(arxivid, version1, version2)
            easy_alignments = easy_align(arxivid, version1, version2)
            process_easy_align(easy_alignments, alignment)

            easy_alignments_outside = easy_align_outside_doc(easy_alignments)
            process_easy_align(easy_alignments_outside, alignment)
            diff._hashable_line_diff.cache_clear()  # clear it after finishing a document

        alignment.write_unaligned_csv()
        alignment.save()


def read_aligned():
    print("Updating models with manual annotations and writing to disk")
    for arxivid, version1, version2 in ids:
        if os.path.isfile(
            data.alignment_finished_path(arxivid, version1, version2)
        ) and os.path.isfile(data.alignment_model_path(arxivid, version1, version2)):
            alignment = Alignment.load(arxivid, version1, version2)

            alignment.read_unaligned_csv()

            alignment.save()


def write_final_aligned():
    print("Writing final annotations to .csv for inspection.")
    for arxivid, version1, version2 in ids:
        if os.path.isfile(
            data.alignment_finished_path(arxivid, version1, version2)
        ) and os.path.isfile(data.alignment_model_path(arxivid, version1, version2)):

            alignment = Alignment.load(arxivid, version1, version2)

            alignment.write_csv()


def main():
    write_unaligned(overwrite=True)

    # read_aligned()

    # write_final_aligned()


if __name__ == "__main__":
    main()
    print("similar()", similar.cache_info())
    print(preprocess_single_sent.cache_info())
    print(diff.sent_filter.cache_info())
