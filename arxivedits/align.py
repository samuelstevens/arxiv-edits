"""
Tries to align the sentences in two versions of a plain text research paper.
"""

from typing import List, Tuple
from collections import namedtuple

import massalign.core as massalign

import lcs
import idf
from tokenizer import ArxivTokenizer

TOKENIZER = ArxivTokenizer()

MISMATCH_PENALTY = 0.1
SKIP_PENALTY = 0

m = massalign.MASSAligner()

# sentence_aligner = massalign.VicinityDrivenSentenceAligner(
#     similarity_model=idf.TFIDFMODEL, acceptable_similarity=0.2, similarity_slack=0.05)

Alignment = namedtuple("Alignment", ["score", "pairs"])

SentenceAlignment = List[Tuple[List[int], List[int]]]


def lcs_align(
    s1: List[str],
    s2: List[str],
    mismatch: float = MISMATCH_PENALTY,
    skip: float = SKIP_PENALTY,
) -> List[Tuple[int, int]]:
    """
    Aligns lists of sentences via a dynamic programming algorithm first described by Regina Barzilay and Noemie Elhadad in Sentence Alignment for Monolingual Comparable Corpora (2003).
    """

    sim = lcs.similarity

    if not s1 or not s2:
        return []

    weighttable: List[List[Alignment]] = [
        [Alignment(0, []) for y in range(len(s2))] for x in range(len(s1))
    ]

    for i, _ in enumerate(s1):
        for j, _ in enumerate(s2):

            bestoption = Alignment(0, [])

            if i == 0 and j == 0:
                # first element, always aligned
                score = sim(s1[i], s2[j]) - mismatch
                if score > bestoption.score:
                    bestoption = Alignment(score, [(i, j)])

            if j >= 1:
                # s(i,j-1) - skip
                score = weighttable[i][j - 1].score - skip
                if score > bestoption.score:
                    bestoption = Alignment(
                        score, weighttable[i][j - 1].pairs + [(i, j)]
                    )

            if i >= 1:
                # s(i-1,j) - skip
                score = weighttable[i - 1][j].score - skip
                if score > bestoption.score:
                    bestoption = Alignment(
                        score, weighttable[i - 1][j].pairs + [(i, j)]
                    )

            if i >= 1 and j >= 1:

                # s(i-1,j-1) + sim(i,j)
                score = weighttable[i - 1][j - 1].score + sim(s1[i], s2[j]) - mismatch
                if score > bestoption.score:
                    bestoption = Alignment(
                        score, weighttable[i - 1][j - 1].pairs + [(i, j)]
                    )

                if j >= 2:
                    # s(i-1,j-2) + sim(i,j) + sim(i,j-1)
                    score = (
                        weighttable[i - 1][j - 2].score
                        + sim(s1[i], s2[j])
                        - mismatch
                        + sim(s1[i], s2[j - 1])
                        - mismatch
                    )

                    if score > bestoption.score:
                        bestoption = Alignment(
                            score, weighttable[i - 1][j - 2].pairs + [(i, j)]
                        )

                if i >= 2:
                    # s(i-2,j-1) + sim(i,j) + sim(i-1,j)
                    score = (
                        weighttable[i - 2][j - 1].score
                        + sim(s1[i], s2[j])
                        - mismatch
                        + sim(s1[i - 1], s2[j])
                        - mismatch
                    )

                    if score > bestoption.score:
                        bestoption = Alignment(
                            score, weighttable[i - 2][j - 1].pairs + [(i, j)]
                        )

                if j >= 2 and i >= 2:  # not the most efficient code
                    # s(i-2,j-2) + sim(i,j-1) + sim(i-1,j)
                    score = (
                        weighttable[i - 2][j - 2].score
                        + sim(s1[i], s2[j - 1])
                        - mismatch
                        + sim(s1[i - 1], s2[j])
                        - mismatch
                    )

                    if score > bestoption.score:
                        bestoption = Alignment(
                            score, weighttable[i - 2][j - 2].pairs + [(i, j)]
                        )

            weighttable[i][j] = bestoption

    return weighttable[-1][-1].pairs


def mass_align(s1: List[str], s2: List[str]) -> List[Tuple[int, int]]:
    """
    Uses MASSAlign to align two lists of sentences
    """

    alignments: SentenceAlignment = []

    alignments, _ = m.getSentenceAlignments(s1, s2, sentence_aligner)

    finalalignments = []

    for pair in alignments:
        if isinstance(pair, tuple):
            a1, a2 = pair
            for i in a1:
                for j in a2:
                    finalalignments.append((i, j))

    return finalalignments


def main():
    """
    """


if __name__ == "__main__":
    main()
