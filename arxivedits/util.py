import os
import pickle
from typing import List, Iterator, Tuple

from arxivedits import data, structures

username = os.getenv("USERNAME") or os.getenv("USER")

with open(
    f"/Users/{username}/Dropbox/arXiv_edit_Sam_Chao/Chao_working_folder/02212020_share_932_doc_groups_with_sam/932.pkl",
    "rb",
) as file:
    chao_data = pickle.load(file)

_good_ids = list(chao_data.keys())
_version_counts = [len(chao_data[arxivid].keys()) + 1 for arxivid in _good_ids]
_good_ids = list(zip(_good_ids, _version_counts))


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


def flatten(nested_list: List[List[structures.T]]) -> List[structures.T]:
    """
    Takes a list of lists and returns a flattened list
    """
    return [item for sublist in nested_list for item in sublist]


def paragraphs_to_lines(doc: List[List[str]]) -> List[str]:
    """
    Like flatten(), but adds a blank line between paragraphs.
    """
    lines = []
    for pg in doc:
        lines.extend(pg)
        lines.append("")

    return lines

