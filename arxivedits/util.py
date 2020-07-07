import os
import pickle
import string
import logging
from typing import List, Iterator, Tuple, Callable, Iterable, Any, Dict, Set

from arxivedits import data
from arxivedits.structures import T, U

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


def flatten(nested_list: List[List[T]]) -> List[T]:
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


def f_mean(a: float, b: float, beta: float) -> float:
    if a + b == 0:
        return 0
    return ((1 + beta * beta) * a * b) / (beta * beta * a + b)


assert f_mean(1, 1, 1) == 1
assert f_mean(0, 0, 1) == 0


def sent_to_words(sent: str) -> List[str]:
    """
    Splits a sentence and removes punctuation.
    """
    return [word for word in sent.split() if word not in string.punctuation]


def sliding_window(
    row: Iterable[T], default_value: Any = None, size: int = 1
) -> Iterator[Tuple[Any, ...]]:
    padding: List[Any] = [default_value] * size

    padded_row: List[Any] = padding + list(row) + padding

    rows: List[List[Any]] = [padded_row[i:] for i in range(size * 2 + 1)]

    return zip(*rows)


def consecutive_values(vector: List[T], test: Callable[[T], bool]) -> List[List[T]]:
    """
    Given a list and a test function, returns a list of groups of consecutive values that pass the test function.
    """

    groups = []
    current_group = []

    for value in vector:
        if test(value):
            current_group.append(value)
        else:
            if current_group:
                groups.append(current_group)
            current_group = []

    if current_group:
        groups.append(current_group)

    return groups


def sent_to_n_grams(sent: str, n: int) -> Iterator[Tuple[str, ...]]:
    """
    Splits a sentence, removes punctuation, and returns a list of tuples of n-grams
    """

    words = [word for word in sent.split() if word not in string.punctuation]

    rows = [words[i:] for i in range(n)]

    return zip(*rows)


def merge_dicts(*dict_args: Dict[T, U]) -> Dict[T, U]:
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in later dicts.
    """
    result: Dict[T, U] = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def get(s: Set[T]) -> T:
    """
    Gets a random element from a set.
    """
    return next(iter(s))


def transpose(a: List[List[T]]) -> List[List[T]]:
    """
    Tranposes a list of lists
    """
    return list(map(list, zip(*a)))


def log_how_many(check_func: Callable[[str, int], bool], verb: str) -> None:
    total = 0
    done = 0
    for a, v in data.get_all_files():
        if check_func(a, v):
            done += 1

    logging.info(f"{done/total*100:.2f}% {verb}.")


if __name__ == "__main__":
    print(sent_to_n_grams("Hello there , I'm General Kenobi .", 2))
