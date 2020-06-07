"""
Defines SimilarityLookup, a lookup structure for sentence similarities.
"""

import os
import pickle
import functools

from typing import Dict, Tuple, List, cast

from tqdm import tqdm

from arxivedits import data, diff, util, similarity


class SimilarityLookup:
    """
    A lookup for similarity between any two sentences.
    """

    def __init__(self, arxivid: str, v1: int, v2: int):
        self.arxivid = arxivid
        self.version1 = v1
        self.version2 = v2

        self.table_name = os.path.join(
            data.ALIGNMENT_DIR, "similarity", f"{arxivid}-{v1}-{v2}-table.pckl",
        )

        self.vector_name = os.path.join(
            data.ALIGNMENT_DIR, "similarity", f"{arxivid}-{v1}-{v2}-vectors.pckl",
        )

        self.table: Dict[
            Tuple[str, str], similarity.Similarity
        ] = self._get_similarity_table()

        self.vectors: Dict[
            str, List[similarity.Similarity]
        ] = self._get_similarity_vectors()

    def _get_similarity_table(self) -> Dict[Tuple[str, str], similarity.Similarity]:
        if os.path.isfile(self.table_name):
            with open(self.table_name, "rb") as file:
                return cast(
                    Dict[Tuple[str, str], similarity.Similarity], pickle.load(file)
                )

        print(f"{self.table_name} does not exist. Creating table from scratch.")

        table = {}

        pgs1 = data.get_paragraphs(self.arxivid, self.version1)

        if isinstance(pgs1, Exception):
            raise pgs1

        lines1 = [
            line for line in util.paragraphs_to_lines(pgs1) if not diff.is_boring(line)
        ]

        pgs2 = data.get_paragraphs(self.arxivid, self.version2)

        if isinstance(pgs2, Exception):
            raise pgs2

        lines2 = [
            line for line in util.paragraphs_to_lines(pgs2) if not diff.is_boring(line)
        ]

        print(f"Iterating through {len(lines1) * len(lines2)} lines.")

        for sent1 in lines1:
            for sent2 in lines2:
                if sent1 == sent2:
                    table[(sent1, sent2)] = similarity.Similarity.identical()
                    continue

                table[(sent1, sent2)] = similarity.get_similarity(sent1, sent2)

        with open(self.table_name, "wb") as file:
            pickle.dump(table, file)

        return table

    def _get_similarity_vectors(self) -> Dict[str, List[similarity.Similarity]]:

        if os.path.isfile(self.vector_name):
            with open(self.vector_name, "rb") as file:
                return cast(Dict[str, List[similarity.Similarity]], pickle.load(file))

        print(f"{self.vector_name} does not exist. Creating vector list from scratch.")

        vectors: Dict[str, List[similarity.Similarity]] = {}

        for sent1, sent2 in self.table:
            assert not diff.is_boring(sent1) and not diff.is_boring(sent2)

            if sent1 not in vectors:
                vectors[sent1] = []

            if sent2 not in vectors:
                vectors[sent2] = []

            vectors[sent1].append(self.table[(sent1, sent2)])
            vectors[sent2].append(self.table[(sent1, sent2)])

        with open(self.vector_name, "wb") as file:
            pickle.dump(vectors, file)

        return vectors

    def get_sentence_vector(self, sentence: str) -> List[similarity.Similarity]:
        """
        Gets a list of Similarity pairs for a given sentence.
        """
        if sentence in self.vectors:
            return self.vectors[sentence]
        else:
            return []

    def write_heatmap(self) -> None:
        """
        Writes a heatmap of itself to an html file.
        """
        raise NotImplementedError()


@functools.lru_cache(maxsize=32)
def load_lookup(arxivid: str, v1: int, v2: int) -> SimilarityLookup:
    return SimilarityLookup(arxivid, v1, v2)


def main() -> None:
    """
    Creates a similarity lookup for every annotated document.
    """
    for arxivid, v1, v2 in tqdm(data.ANNOTATED_IDS):
        SimilarityLookup(arxivid, v1, v2)


if __name__ == "__main__":
    main()
