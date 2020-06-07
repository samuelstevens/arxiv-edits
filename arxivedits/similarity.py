import functools

from typing import Set, Any, Iterable

from dataclasses import dataclass

from arxivedits import alignment, diff, util


@dataclass
class Similarity:
    jaccard_sim: float
    diff_sim: float
    jaccard_2_gram_sim: float
    diff_2_gram_sim: float
    # tfidf_sim: float

    @staticmethod
    def default() -> "Similarity":
        return Similarity(0, 0, 0, 0)

    @staticmethod
    def identical() -> "Similarity":
        return Similarity(1, 1, 1, 1)


def get_jaccard_sim(A: Set[Any], B: Set[Any]) -> float:
    if not A or not B:
        return 0
    return len(A & B) / len(A | B)


def get_diff_sim(a: Iterable[Any], b: Iterable[Any]) -> float:
    diff_output = diff.line_diff(list(a), list(b))

    length_removed = len([1 for code, _ in diff_output if code == -1])
    length_original = len([1 for code, _ in diff_output if code in [-1, 0]])
    length_added = len([1 for code, _ in diff_output if code == 1])
    length_new = len([1 for code, _ in diff_output if code in [1, 0]])

    if not length_original or not length_new:
        return 0

    return 1 - (length_removed / length_original + length_added / length_new) / 2


@functools.lru_cache(maxsize=512)
def get_similarity(sent1: str, sent2: str) -> Similarity:
    if not sent1 or sent1.isspace() or not sent2 or sent2.isspace():
        return Similarity.default()

    if sent1 == sent2:
        return Similarity.identical()

    try:
        sent1 = alignment.util.preprocess_single_sent(sent1)
        sent2 = alignment.util.preprocess_single_sent(sent2)
    except Exception as err:
        print(sent1, len(sent1))
        print(sent2, len(sent2))
        raise err

    if not sent1 or sent1.isspace() or not sent2 or sent2.isspace():
        return Similarity.default()

    if sent1 == sent2:
        return Similarity.identical()

    jaccard_sim = get_jaccard_sim(
        set(util.sent_to_words(sent1)), set(util.sent_to_words(sent2)),
    )

    diff_sim = get_diff_sim(util.sent_to_words(sent1), util.sent_to_words(sent2))

    jaccard_2_gram_sim = get_jaccard_sim(
        set(util.sent_to_n_grams(sent1, 2)), set(util.sent_to_n_grams(sent2, 2))
    )

    diff_2_gram_sim = get_diff_sim(
        util.sent_to_n_grams(sent1, 2), util.sent_to_n_grams(sent2, 2)
    )

    return Similarity(
        jaccard_sim=jaccard_sim,
        jaccard_2_gram_sim=jaccard_2_gram_sim,
        diff_sim=diff_sim,
        diff_2_gram_sim=diff_2_gram_sim,
    )


def main() -> None:
    sent1 = "The interference quenching is apparent in the double-slit experiment, where the elimination of interference fringes gives rise to a classical-like pattern where the classical addition rule of probabilities holds."
    sent2 = "Here we have dealt with the problem of the damping or quenching of the interference fringes produced by decoherence in a two-slit experiment under the presence of an environment, which yields as a result a classical-like pattern."

    print(sent1)
    print(sent2)
    print(get_similarity(sent1, sent2))
    print()

    sent1 = "Figure 2 shows the variation of the parameters [MATH] and [MATH] with time [MATH] where we observe that the values of these parameters increase with time leading to a decrease in the conductance which is found to be consistent with the experiment."
    sent2 = "This reduces the hole carrier concentration and hence the conductance of the SWCNT, which is consistent with the experiment."

    print(sent1)
    print(sent2)
    print(get_similarity(sent1, sent2))
    print()

    sent1 = "In order to elucidate and understand how decoherence causes this interference quenching, we have considered here the simple trajectory based models mentioned above."
    sent2 = "In order to elucidate and understand decoherence without taking into account explicitly the dynamics of the environment degrees of freedom, we have considered some simple reduced quantum-trajectory models."

    print(sent1)
    print(sent2)
    print(get_similarity(sent1, sent2))
    print()

    sent1 = "We investigate the role of retardation corrections to polarizability and to refractive index."
    sent2 = "We found that the classical electromagnetic theory of dielectrics requires corresponding modifications in terms of nonlocality of the dielectric constant."

    print(sent1)
    print(sent2)
    print(get_similarity(sent1, sent2))
    print()


if __name__ == "__main__":
    main()
