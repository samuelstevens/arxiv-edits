"""
Evaluates MASSAlign vs weighted-LCS on a manually aligned dataset
"""

import os
import pathlib
import json
import time
import re
import random
import csv
from typing import Tuple, Callable, List, Dict

import requests

import arxivedits.data as data
import arxivedits.stats as stats
import arxivedits.align as align
import arxivedits.source as source
import arxivedits.tex as tex
import arxivedits.tokenizer as tokenizer

Algorithm = Callable[[List[str], List[str]], List[Tuple[int, int]]]


class Evaluation:
    """
    True/false positive/negative results for an algorithm
    """

    def __init__(self, algorithm: Algorithm):
        self.algorithm = algorithm
        self.TP = 0
        self.FP = 0
        self.TN = 0
        self.FN = 0
        self.precision: float = 0
        self.recall: float = 0
        self.f1: float = 0

    def add_results(self, TP: int, FP: int, TN: int, FN: int):
        """
        Adds a number of true/false positive/negative results
        """
        self.TP += TP
        self.FP += FP
        self.TN += TN
        self.FN += FN

        if self.TP + self.FP > 0:
            self.precision = self.TP / (self.TP + self.FP)
        if self.TP + self.FN > 0:
            self.recall = self.TP / (self.TP + self.FN)
        if self.precision + self.recall > 0:
            self.f1 = (
                2 * (self.precision * self.recall) / (self.precision + self.recall)
            )

    def display(self, verbose=False):
        """
        Displays results to stdout
        """
        print(self.algorithm.__name__)
        if verbose:
            print(f"TP: {self.TP}")
            print(f"FP: {self.FP}")
            print(f"TN: {self.TN}")
            print(f"FN: {self.FN}")
        print(f"Precision: {self.precision:.2f}")
        print(f"Recall:    {self.recall:.2f}")
        print(f"F1:        {self.f1:.2f}")


def evaluate_algorithm(
    algorithm: Algorithm,
    sentenceset1: List[str],
    sentenceset2: List[str],
    alignment: Dict[Tuple[int, int], int],
) -> Tuple[int, int, int, int]:
    """
    Calculates TP, FP, TN, FN for an alignment algorithm.
    """

    predicted = {k: 0 for k in alignment}

    TP, FP, TN, FN = 0, 0, 0, 0

    for k in algorithm(sentenceset1, sentenceset2):
        predicted[k] = 1

    for k in predicted:
        if k not in alignment:
            raise Exception(
                f"Algorithm produced alignment {k} not found in gold alignment."
            )

        # check if it was a true positive, true negative, false positive, or false negative.

        if predicted[k] == 1 and alignment[k] == 1:
            # true positive
            TP += 1
        elif predicted[k] == 1 and alignment[k] == 0:
            # false positive
            FP += 1
            print(f"{algorithm.__name__} incorrectly aligned these sentences.")
            print(sentenceset1[k[0]])
            print(sentenceset2[k[1]])
            print()
        elif predicted[k] == 0 and alignment[k] == 0:
            # true negative
            TN += 1
        elif predicted[k] == 0 and alignment[k] == 1:
            # false negative
            FN += 1
            print(f"{algorithm.__name__} incorrectly didn't align these sentences.")
            print(sentenceset1[k[0]])
            print(sentenceset2[k[1]])
            print()
        else:
            print("Error:", k, predicted[k], alignment[k])

    return (TP, FP, TN, FN)


def parse_aligned_name(name: str) -> Tuple[str, int, int]:
    """
    1701.01370-v1-v2 -> (1701.01370, 1, 2)
    cond-mat-0407626-v1-v2 -> (cond-mat-0407626, 1, 2)
    """

    *namelist, v1, v2 = name.split("-")

    name = "-".join(namelist)

    return name, int(v1[1]), int(v2[1])


def main():
    """
    Evaluates success of alignment algorithms based on manually aligned datasets
    """

    pwd = pathlib.Path(__file__).parent
    alignmentsdir = os.path.join(pwd, "data", "alignments")

    algorithms = [align.mass_align, align.lcs_align]
    evaluations = [Evaluation(a) for a in algorithms]

    finalpositive = 0
    finalnegative = 0

    for foldername in os.listdir(alignmentsdir):
        arxivid, v1, v2 = parse_aligned_name(foldername)

        folderpath = os.path.join(alignmentsdir, foldername)

        for sectionfile in os.listdir(folderpath):
            filepath = os.path.join(folderpath, sectionfile)

            with open(filepath, "r") as file:
                lines = file.read().splitlines()

            section1, section2 = lines[1].split(" | ")

            # I will now get the gold alignment
            alignment = {}
            for line in lines[2:]:
                i1, i2, value = line[1:-1].split(", ")
                i1 = int(i1)
                i2 = int(i2)
                value = int(value)
                alignment[(i1, i2)] = value

            # Now I have the paper id, the versions, and the sections.
            # I will retrieve the sections from the tmp data folder

            v1filename = os.path.join(data.SENTENCES_DIR, f"{arxivid}-v{v1}.json")
            v2filename = os.path.join(data.SENTENCES_DIR, f"{arxivid}-v{v2}.json")

            with open(v1filename, "r") as file:
                v1sentences = json.load(file)

            with open(v2filename, "r") as file:
                v2sentences = json.load(file)

            for section in v1sentences:
                if section[0] == section1:
                    v1sentences = section[1]
                    break

            if not v1sentences:
                raise Exception(f"Did not find section {section1} in {v1filename}")

            for section in v2sentences:
                if section[0] == section2:
                    v2sentences = section[1]
                    break

            if not v2sentences:
                raise Exception(f"Did not find section {section2} in {v2filename}")

            # I now have two lists of sentences.
            # I need to test the alignment algorithm.
            for e in evaluations:
                print(f"--- {section1}, {v1filename} ---")
                results = evaluate_algorithm(
                    e.algorithm, v1sentences, v2sentences, alignment
                )
                e.add_results(*results)
                finalpositive += results[0] + results[3]
                finalnegative += results[1] + results[2]

        print(f"{arxivid} evaluated.")
        for e in evaluations:
            e.display()
        print()

    print()
    print("Final Results:")
    for e in evaluations:
        e.display(verbose=True)

    finalnegative /= len(algorithms)
    finalpositive /= len(algorithms)

    print(f"Positive targets: {finalpositive}")
    print(f"Negative targets: {finalnegative}")


def evaluate_detex() -> None:
    """
    Creates three versions of a detexed-paper and puts it in a location with a pdf file for comparison.

    `detex.txt`: each line is a sentence. Formed by using `opendetex` and then the `CoreNLP` tokenizer to split into sentences.

    `pandoc.md`: formed via `pandoc --to markdown`.

    `chenhao.txt`: formed via Chenhao's `simpleLatexToText()`.
    """

    sample = stats.get_random_sample(multipleversions=True)

    # take a smaller sample
    sample = sample[50:70]

    # sample = [("0806.0232", 2)]

    sample = [s for s in sample if source.is_extracted(*s)]

    tok = tokenizer.CoreNLPTokenizer()

    for arxivid, versioncount in sample:
        v = versioncount
        arxividpath = arxivid.replace("/", "-")
        sourcefile = f"{arxividpath}-v{v}"

        sourcefilepath = os.path.join(data.UNZIPPED_DIR, sourcefile)
        os.makedirs(os.path.join(data.TEXT_DIR, sourcefile), exist_ok=True)

        # test detex

        # pandoc.md
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "pandoc.md")
        err = tex.pandoc_file(sourcefilepath, outputfilepath)
        if err:
            print(err)

        # pandoc.txt
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "pandoc.txt")
        err = tex.pandoc_file(sourcefilepath, outputfilepath, to="plain")
        if err:
            print(err)

        # opendetex.txt
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "opendetex.txt")
        tex.detex_file(sourcefilepath, outputfilepath, clean=False)

        with open(outputfilepath, "r") as file:
            paragraphs = file.read().split("\n\n")

        # opendetex-tokenized.txt
        outputfilepath = os.path.join(
            data.TEXT_DIR, sourcefile, "opendetex-tokenized.txt"
        )

        paragraphs = [" ".join(p.split("\n")).strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if p]

        with open(outputfilepath, "w") as file:
            for p in paragraphs:
                try:

                    sentences = tok.tokenize(p).ssplit()

                    for s in sentences:
                        file.write(s + "\n")
                    file.write("\n")
                except AttributeError:
                    print("Error:")
                    print(p)

        # opendetex-updated.txt
        outputfilepath = os.path.join(
            data.TEXT_DIR, sourcefile, "opendetex-updated.txt"
        )
        tex.detex_file(sourcefilepath, outputfilepath)

        with open(outputfilepath, "r") as file:
            paragraphs = file.read().split("\n\n")

        # opendetex-tokenized-updated.txt
        outputfilepath = os.path.join(
            data.TEXT_DIR, sourcefile, "opendetex-tokenized-updated.txt"
        )

        paragraphs = [" ".join(p.split("\n")).strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if p]
        paragraphs = [re.sub(r" +", " ", p, flags=re.MULTILINE) for p in paragraphs]

        with open(outputfilepath, "w") as file:
            for p in paragraphs:
                try:

                    sentences = tok.tokenize(p).ssplit()

                    for s in sentences:
                        file.write(s + "\n")
                    file.write("\n")
                except AttributeError:
                    print("Error:")
                    print(p)

        # chenhao.txt
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "chenhao.txt")
        tex.simpleLatexToText(sourcefilepath, outputfilepath, sectioned=True)

        # clean-tex.tex
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "clean-tex.tex")
        with open(sourcefilepath, "r") as infile:
            with open(outputfilepath, "w") as outfile:
                outfile.write(tex.clean(infile.read()))

        # original-tex.tex
        outputfilepath = os.path.join(data.TEXT_DIR, sourcefile, "original-tex.tex")
        with open(sourcefilepath, "r") as infile:
            with open(outputfilepath, "w") as outfile:
                outfile.write(infile.read())

        # download PDF
        url = f"https://arxiv.org/pdf/{arxivid}v{v}"
        localpath = os.path.join(data.TEXT_DIR, sourcefile, f"{sourcefile}.pdf")
        if not os.path.isfile(localpath):
            try:
                source.download_file(url, localpath)
                time.sleep(1)
            except requests.exceptions.HTTPError:
                pass


def random_sample_comparison(length=10):
    if os.path.isdir("scripts"):
        return

    ids = data.get_local_files(maximum_only=True)

    random.shuffle(ids)

    with open("data/sample-only-multiversion.csv") as csvfile:
        reader = csv.reader(csvfile)
        validids = set([tuple(pair) for pair in reader])

    ids = [
        (arxivid, versionmax)
        for arxivid, versionmax in validids
        if os.path.isfile(data.sentence_path(arxivid, 1))
        and os.path.isfile(data.sentence_path(arxivid, 2))
    ]

    ids = ids[0:100]

    os.makedirs("scripts", exist_ok=True)

    for current_batch in range(len(ids) // length):
        filepath = (
            f"scripts/open-{current_batch * length}-{(current_batch + 1) * length}.sh"
        )
        with open(filepath, "w") as scriptfile:

            scriptfile.write("#!/usr/bin/env bash\n")

            for i in range(current_batch * length, (current_batch + 1) * length):
                arxivid, _ = ids[i]
                scriptfile.write(
                    f"code --diff {data.sentence_path(arxivid, 1)} {data.sentence_path(arxivid, 2)}\n"
                )

        os.chmod(filepath, 0o777)


if __name__ == "__main__":
    # main()
    # evaluate_detex()
    random_sample_comparison()
