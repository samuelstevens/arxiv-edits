from dataclasses import dataclass

from typing import List

from arxivedits.similarity import Similarity
from arxivedits import alignment
from arxivedits.detex.constants import (
    CITE_TAG,
    BLOCK_MATH_TAG,
    INLINE_MATH_TAG,
    REF_TAG,
)


@dataclass
class FeatureVector:
    n_tokens: int
    n_special_tokens: int
    max_diff_sim: float
    avg_diff_sim: float
    max_diff_2_gram_sim: float
    avg_diff_2_gram_sim: float
    max_jaccard_sim: float
    avg_jaccard_sim: float
    max_jaccard_2_gram_sim: float
    avg_jaccard_2_gram_sim: float
    percent_special_tokens: float

    def to_list(self) -> List[float]:
        """
        Returns a list of parameters representing the vector.
        """
        return [
            self.max_diff_sim,
            self.avg_diff_sim,
            self.max_diff_2_gram_sim,
            self.avg_diff_2_gram_sim,
            self.max_jaccard_sim,
            self.avg_jaccard_sim,
            self.max_jaccard_2_gram_sim,
            self.avg_jaccard_2_gram_sim,
            self.n_tokens,
            self.n_special_tokens,
            self.percent_special_tokens,
        ]

    @staticmethod
    def default() -> "FeatureVector":
        """
        A empty, or default feature vector.
        """
        return FeatureVector(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def get_max_field(similarity_vector: List[Similarity], field: str) -> float:
    return (
        getattr(max(similarity_vector, key=lambda sim: getattr(sim, field)), field)
        if similarity_vector
        else 0
    )


def get_avg_field(similarity_vector: List[Similarity], field: str) -> float:
    return (
        sum([getattr(sim, field) for sim in similarity_vector]) / len(similarity_vector)
        if similarity_vector
        else 0
    )


def make_feature_vector(
    sentence: str, similarity_vector: List[Similarity]
) -> FeatureVector:
    """
    Given a sentence and its neighbours, creates the feature vector for the linear model.
    """

    tokens = [
        tok for tok in alignment.util.preprocess_single_sent(sentence).split(" ") if tok
    ]

    n_tokens = len(tokens)
    n_special_tokens = len(
        [
            tok
            for tok in tokens
            if INLINE_MATH_TAG in tok
            or BLOCK_MATH_TAG in tok
            or CITE_TAG in tok
            or REF_TAG in tok
        ]
    )

    return FeatureVector(
        max_diff_sim=get_max_field(similarity_vector, "diff_sim"),
        avg_diff_sim=get_avg_field(similarity_vector, "diff_sim"),
        max_diff_2_gram_sim=get_max_field(similarity_vector, "diff_2_gram_sim"),
        avg_diff_2_gram_sim=get_avg_field(similarity_vector, "diff_2_gram_sim"),
        max_jaccard_sim=get_max_field(similarity_vector, "jaccard_sim"),
        avg_jaccard_sim=get_avg_field(similarity_vector, "jaccard_sim"),
        max_jaccard_2_gram_sim=get_max_field(similarity_vector, "jaccard_2_gram_sim"),
        avg_jaccard_2_gram_sim=get_avg_field(similarity_vector, "jaccard_2_gram_sim"),
        n_tokens=n_tokens,
        n_special_tokens=n_special_tokens,
        percent_special_tokens=n_special_tokens / n_tokens if n_tokens else 0,
    )


if __name__ == "__main__":
    pass
