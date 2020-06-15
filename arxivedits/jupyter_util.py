import os

import pickle
from typing import Iterator, Tuple

from arxivedits import data

USERNAME = os.getenv("USERNAME") or os.getenv("USER")

with open(
    f"/Users/{USERNAME}/Dropbox/arXiv_edit_Sam_Chao/Chao_working_folder/02212020_share_932_doc_groups_with_sam/932.pkl",
    "rb",
) as file:
    CHAO_DATA = pickle.load(file)

_good_ids = list(CHAO_DATA.keys())
_version_counts = [len(CHAO_DATA[arxivid].keys()) + 1 for arxivid in _good_ids]
_good_ids = list(zip(CHAO_DATA, _version_counts))


def good_id_iter() -> Iterator[Tuple[str, int, int]]:
    for arxivid, version_count in _good_ids:
        for v1 in range(1, version_count):
            v2 = v1 + 1
            if not os.path.isfile(
                data.sentence_path(arxivid, v1)
            ) or not os.path.isfile(data.sentence_path(arxivid, v2)):
                print(
                    f"{os.path.isfile(data.sentence_path(arxivid, v1))} {os.path.isfile(data.sentence_path(arxivid, v2))}"
                )
                # should never ever print this out, because good_ids are only valid ids
                continue

            yield arxivid, v1, v2


good_id_len = len(list(good_id_iter()))
