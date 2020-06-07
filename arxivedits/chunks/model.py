import os
import csv
from typing import Tuple, List

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np


from tqdm import tqdm

from arxivedits import data
from arxivedits.chunks.data import group_asserts


def parse_row(row: List[str]) -> List[float]:
    return [float(i) for i in row]


def get_data(
    group: str, min_length: int, window_size: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns the positive and negative training examples and labels for a group (either 'removed', 'added', or 'both)
    """

    group_asserts(group, both=True)

    added_filename = os.path.join(
        data.ALIGNMENT_DIR,
        "chunks",
        "data",
        f"added-examples-{window_size}-{min_length}.csv",
    )

    removed_filename = os.path.join(
        data.ALIGNMENT_DIR,
        "chunks",
        "data",
        f"removed-examples-{window_size}-{min_length}.csv",
    )

    with open(removed_filename, "r") as file:
        csvreader = csv.reader(file, dialect="excel")
        added_rows = list(csvreader)

    with open(added_filename, "r") as file:
        csvreader = csv.reader(file, dialect="excel")
        removed_rows = list(csvreader)

    if group == "removed":
        rows = removed_rows
    elif group == "added":
        rows = added_rows
    else:
        rows = added_rows + removed_rows

    X = np.zeros((len(rows), len(rows[0]) - 1))
    Y = np.zeros((len(rows),))

    for i, row in enumerate(rows):
        *features, target = parse_row(row)
        X[i] = features
        Y[i] = target

    return X, Y


def train_model(
    group: str, min_length: int, window_size: int, silent: bool = True,
) -> Tuple[LogisticRegression, float]:
    group_asserts(group, both=True)

    X, Y = get_data(group, min_length, window_size)

    model = LogisticRegression(random_state=0, solver="liblinear")
    scores = cross_val_score(model, X, Y, cv=10)

    if not silent:
        print(f"'{group}' accuracy: {np.mean(scores):.5f} (on 10-Fold CV)")

    model.fit(X, Y)

    return model, np.mean(scores)


def grid_search(group: str) -> None:
    group_asserts(group, both=True)

    max_score = 0.0
    best_params = (-1, -1)

    for length in tqdm(range(5, 13)):
        for window in range(1, 4):
            _, score = train_model(group, min_length=length, window_size=window)
            if score > max_score:
                max_score = score
                best_params = (length, window)

    print(group, max_score, best_params)


if __name__ == "__main__":
    grid_search("added")
    grid_search("removed")
    grid_search("both")
