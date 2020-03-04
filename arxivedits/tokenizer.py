# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""
Base tokenizer/tokens classes and utilities.
"""

from functools import reduce
from typing import List
import json
import copy
import os
import re
import pathlib
import string

import pexpect

# from nltk.tokenize.treebank import TreebankWordTokenizer
from nltk import word_tokenize
import nltk.data

from arxivedits.detex.constants import BLOCK_MATH_TAG
from arxivedits import data
from arxivedits.structures import ArxivID

FALSE_SPLIT_SUFFIXES = set(
    [
        # figures
        "Fig.",
        "Figs.",
        "fig.",
        "figs.",
        # sections
        "Sec.",
        "Secs.",
        "sec.",
        "secs.",
        # references
        "Ref.",
        "Refs.",
        "ref.",
        "refs.",
        # equations
        "Eq.",
        "Eqs.",
        "eq.",
        "eqs.",
        "Eqn.",
        "Eqns.",
        "eqn.",
        "eqns.",
        # misc.
        "et al.",
        "resp.",
    ]
)
FALSE_SPLIT_PUNC = set([".", "(", "["])


class Tokens:
    """
    A class to represent a list of tokenized text.
    """

    TEXT = 0
    TEXT_WS = 1
    SPAN = 2
    POS = 3
    LEMMA = 4
    NER = 5

    def __init__(self, data, annotators, opts=None, output=None):
        self.data = data
        self.annotators = annotators
        self.opts = opts or {}
        if output:
            self.output = output

        # might want to use /\d+\w+\./ as a regex match for references that cause splitting as well, but only if the next letter is lowercase.
        self.false_split_suffixes = FALSE_SPLIT_SUFFIXES
        self.false_split_punc = FALSE_SPLIT_PUNC

    def __len__(self):
        """
        The number of tokens.
        """
        return len(self.data)

    def slice(self, i=None, j=None):
        """
        Return a view of the list of tokens from [i, j).
        """
        new_tokens = copy.copy(self)
        new_tokens.data = self.data[i:j]
        return new_tokens

    def ssplit(self):
        sentence_list = []
        original_sentence = self.untokenize()
        dict_a = self.output

        for sentence in dict_a["sentences"]:
            start_offset = sentence["tokens"][0]["characterOffsetBegin"]
            end_offset = sentence["tokens"][-1]["characterOffsetEnd"]
            sentence_list.append(
                original_sentence[start_offset : end_offset + 1].strip()
            )

        def join_sentences(sentences: List[str], newsentence: str) -> List[str]:
            newsentence = " ".join(newsentence.split())

            if newsentence == ".":
                return sentences

            newsentences = split_on_tag(BLOCK_MATH_TAG, newsentence)

            if not sentences:
                return newsentences

            last_sentence = sentences[-1]

            # handles cases like "... in Fig. 3."
            for suf in self.false_split_suffixes:
                if last_sentence.endswith(suf):
                    sentences[-1] = last_sentence + " " + newsentences[0]
                    return sentences + newsentences[1:]

            # cases like "... in Fig.(3)." -> "... in Fig.(" + "(3)."
            for suf in self.false_split_suffixes:
                for punc in self.false_split_punc:
                    if last_sentence.endswith(
                        f"{suf}{punc}"
                    ) and newsentence.startswith(punc):
                        sentences[-1] = last_sentence + newsentences[0][1:]
                        return sentences + newsentences[1:]

            return sentences + newsentences

        def split_on_tag(tag: str, text: str, offset: int = 0) -> List[str]:

            if tag in text[offset:]:

                nextsentence = text.index(tag, offset) + len(tag)

                if nextsentence + 1 >= len(text):
                    return [text]

                # if the next letter after the tag is uppercase, split.
                if text[nextsentence + 1] in string.ascii_uppercase:
                    return [
                        text[:nextsentence],
                        *split_on_tag(tag, text[nextsentence:].lstrip()),
                    ]

                # else try and split further on
                return split_on_tag(tag, text, nextsentence + 1)

            return [text]

        return reduce(join_sentences, sentence_list, [])

    def untokenize(self):
        """
        Returns the original text (with whitespace reinserted).
        """
        return "".join([t[self.TEXT_WS] for t in self.data]).strip()

    def words(self, uncased=False):
        """
        Returns a list of the text of each token

        Args:
            uncased: lower cased text
        """
        if uncased:
            return [t[self.TEXT].lower() for t in self.data]

        return [t[self.TEXT] for t in self.data]

    def offsets(self):
        """
        Returns a list of [start, end) character offsets of each token.
        """
        return [t[self.SPAN] for t in self.data]

    def pos(self):
        """
        Returns a list of part-of-speech tags of each token.
        Returns None if this annotation was not included.
        """
        if "pos" not in self.annotators:
            return None
        return [t[self.POS] for t in self.data]

    def lemmas(self):
        """
        Returns a list of the lemmatized text of each token.
        Returns None if this annotation was not included.
        """
        if "lemma" not in self.annotators:
            return None
        return [t[self.LEMMA] for t in self.data]

    def entities(self):
        """
        Returns a list of named-entity-recognition tags of each token.
        Returns None if this annotation was not included.
        """
        if "ner" not in self.annotators:
            return None
        return [t[self.NER] for t in self.data]

    def ngrams(self, n=1, uncased=False, filter_fn=None, as_strings=True):
        """
        Returns a list of all ngrams from length 1 to n.

        Args:
            n: upper limit of ngram length
            uncased: lower cases text
            filter_fn: user function that takes in an ngram list and returns
              True or False to keep or not keep the ngram
            as_string: return the ngram as a string vs list
        """

        def _skip(gram):
            if not filter_fn:
                return False
            return filter_fn(gram)

        words = self.words(uncased)
        ngrams = [
            (s, e + 1)
            for s in range(len(words))
            for e in range(s, min(s + n, len(words)))
            if not _skip(words[s : e + 1])
        ]

        # Concatenate into strings
        if as_strings:
            ngrams = ["{}".format(" ".join(words[s:e])) for (s, e) in ngrams]

        return ngrams

    def entity_groups(self):
        """
        Group consecutive entity tokens with the same NER tag.
        """

        entities = self.entities()
        if not entities:
            return None
        non_ent = self.opts.get("non_ent", "O")
        groups = []
        idx = 0
        while idx < len(entities):
            ner_tag = entities[idx]
            # Check for entity tag
            if ner_tag != non_ent:
                # Chomp the sequence
                start = idx
                while idx < len(entities) and entities[idx] == ner_tag:
                    idx += 1
                groups.append((self.slice(start, idx).untokenize(), ner_tag))
            else:
                idx += 1
        return groups


class Tokenizer:
    """
    Base tokenizer class.
    Tokenizers implement tokenize, which should return a Tokens class.
    """

    def tokenize(self, text) -> Tokens:
        raise NotImplementedError

    def shutdown(self):
        pass

    def __del__(self):
        self.shutdown()


class CoreNLPTokenizer(Tokenizer):
    """
    Simple wrapper around the Stanford CoreNLP pipeline.

    Serves commands to a java subprocess running the jar. Requires Java 8.

    Written by Chao Jiang
    """

    def __init__(self, **kwargs):
        """
        Args:
            annotators: set that can include pos, lemma, and ner.
            classpath: Path to the corenlp directory of jars
            mem: Java heap memory
        """

        self.classpath = "/Users/samstevens/Java/stanford-corenlp/*"
        self.annotators = copy.deepcopy(kwargs.get("annotators", set()))
        self.mem = kwargs.get("mem", "2g")

        with open(
            os.path.join(pathlib.Path(__file__).parent, "data", "latex-unicode.json"),
            "r",
        ) as file:
            self.latex = json.load(file)

        self._launch()

    def _launch(self):
        """
        Start the CoreNLP jar with pexpect.
        """

        annotators = ["tokenize", "ssplit"]
        if "ner" in self.annotators:
            annotators.extend(["pos", "lemma", "ner"])
        elif "lemma" in self.annotators:
            annotators.extend(["pos", "lemma"])
        elif "pos" in self.annotators:
            annotators.extend(["pos"])
        annotators = ",".join(annotators)
        options = ",".join(["untokenizable=noneDelete", "invertible=true"])
        cmd = [
            "java",
            "-mx" + self.mem,
            "-cp",
            f'"{self.classpath}"',
            "edu.stanford.nlp.pipeline.StanfordCoreNLP",
            "-annotators",
            annotators,
            "-tokenize.options",
            options,
            "-outputFormat",
            "json",
            "-prettyPrint",
            "false",
        ]

        # We use pexpect to keep the subprocess alive and feed it commands.
        # Because we don't want to get hit by the max terminal buffer size,
        # we turn off canonical input processing to have unlimited bytes.
        self.corenlp = pexpect.spawn("/bin/bash", maxread=100000, timeout=60)
        self.corenlp.setecho(False)
        self.corenlp.sendline("stty -icanon")
        self.corenlp.sendline(" ".join(cmd))
        self.corenlp.delaybeforesend = 0
        self.corenlp.delayafterread = 0
        self.corenlp.expect_exact("NLP>", searchwindowsize=100)

    @staticmethod
    def _convert(token):
        if token == "-LRB-":
            return "("
        if token == "-RRB-":
            return ")"
        if token == "-LSB-":
            return "["
        if token == "-RSB-":
            return "]"
        if token == "-LCB-":
            return "{"
        if token == "-RCB-":
            return "}"
        return token

    def _process(self, text: str) -> str:
        """
        Takes text and removes block math ($$...$$) and tries to reduce inline math ($...$) as much as possible.
        """
        text = text.replace("\n", " ")

        blockpattern = re.compile(r"\$\$(.*)\$\$")
        text = blockpattern.sub("", text)

        inlinepattern = re.compile(r"\$(.*?)\$")

        output = ""
        cur = 0

        for match in inlinepattern.finditer(text):
            for i, group in enumerate(match.groups()):
                if group in self.latex:
                    start, end = match.span(i)
                    output += text[cur:start]
                    output += self.latex[group]
                    cur = end
                elif len(group) == 1:
                    start, end = match.span(i)
                    output += text[cur:start]
                    output += group
                    cur = end
                else:
                    try:
                        float(group)
                    except ValueError:
                        pass
                    else:
                        start, end = match.span(i)
                        output += text[cur:start]
                        output += group
                        cur = end

        output += text[cur:]
        return output

    def tokenize(self, text: str) -> Tokens:
        # Since we're feeding text to the commandline, we're waiting on seeing
        # the NLP> prompt. Hacky!
        if "NLP>" in text:
            raise RuntimeError("Bad token (NLP>) in text!")

        # Sending q will cause the process to quit -- manually override
        if text.lower().strip() == "q":
            token = text.strip()
            index = text.index(token)
            data = [(token, text[index:], (index, index + 1), "NN", "q", "O")]
            return Tokens(data, self.annotators)

        # Minor cleanup before tokenizing.
        cleant = self._process(text)

        self.corenlp.sendline(cleant.encode("utf-8"))
        self.corenlp.expect_exact("NLP>", searchwindowsize=100)

        # Skip to start of output (may have been stderr logging messages)
        output = self.corenlp.before
        start = output.find(b'{\r\n  "sentences":')
        output = json.loads(output[start:].decode("utf-8"))

        data = []
        tokens = [t for s in output["sentences"] for t in s["tokens"]]
        # print(output)
        for i, _ in enumerate(tokens):
            # Get whitespace
            start_ws = tokens[i]["characterOffsetBegin"]
            if i + 1 < len(tokens):
                end_ws = tokens[i + 1]["characterOffsetBegin"]
            else:
                end_ws = tokens[i]["characterOffsetEnd"]

            data.append(
                (
                    self._convert(tokens[i]["word"]),
                    cleant[start_ws:end_ws],
                    (
                        tokens[i]["characterOffsetBegin"],
                        tokens[i]["characterOffsetEnd"],
                    ),
                    tokens[i].get("pos", None),
                    tokens[i].get("lemma", None),
                    tokens[i].get("ner", None),
                )
            )
        return Tokens(data, self.annotators, output=output)


class ArxivTokenizer:
    """
    A sentence and word tokenizer with several hand-coded rules specific to Arxiv/LaTeX documents.
    """

    def __init__(self, annotators=None):
        self.detector = nltk.data.load("tokenizers/punkt/english.pickle")

        # might want to use /\d+\w+\./ as a regex match for references that cause splitting as well, but only if the next letter is lowercase.
        self.false_split_suffixes = FALSE_SPLIT_SUFFIXES

        self.annotators = annotators or set()

    def __split_sent(self, text: str) -> List[str]:
        split = self.detector.tokenize(text.replace("\n", " "))

        def join_sentences(sentences: List[str], newsentence: str) -> List[str]:
            if not sentences:
                return [newsentence]

            lastsentence = sentences[-1]

            for suf in self.false_split_suffixes:
                if lastsentence.endswith(suf):
                    sentences[-1] = lastsentence + " " + newsentence
                    return sentences

            return sentences + [newsentence]

        return reduce(join_sentences, split, [])

    def __split_word(self, sentence: str) -> List[str]:
        """
        Splits a sentence into words.
        """
        return word_tokenize(sentence)

    def split(self, text: str, group="") -> List[str]:
        """
        Splits text by either 'sentence' or 'word'.
        """
        if group == "sentence":
            return self.__split_sent(text)
        if group == "word":
            return self.__split_word(text)

        raise ValueError("group must be either 'sentence' or 'word'.")


def is_sentenced(arxividpath: ArxivID, version: int) -> bool:
    return os.path.isfile(data.sentence_path(arxividpath, version))


def tokenize_file(inputfilepath: str, outputfilepath: str, tok=CoreNLPTokenizer()):
    with open(inputfilepath, "r") as textfile:
        paragraphs = textfile.read().split("\n\n")

    paragraphs = [" ".join(p.split("\n")).strip() for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]

    with open(outputfilepath, "w") as sentencefile:
        for p in paragraphs:
            try:
                sentences = tok.tokenize(p).ssplit()

                for s in sentences:
                    sentencefile.write(s + "\n")
                sentencefile.write("\n")

            except AttributeError as err:
                print(f"Error on {textfilepath}: {err}")


def main():
    """
    Converts information in detexed text to sentences.
    """

    tok = CoreNLPTokenizer()

    for arxivid, version in [("0705.2267", 5)]:  # data.get_sample_files():
        textfilepath = data.text_path(arxivid, version)
        sentencefilepath = data.sentence_path(arxivid, version)

        if not os.path.isfile(textfilepath):
            # print(f"{arxivid}-v{version} was not converted to text.")
            continue

        # if os.path.isfile(sentencefilepath):
        #     continue
        print(textfilepath)
        tokenize_file(textfilepath, sentencefilepath, tok)
        print(sentencefilepath)
        print(data.latex_path(arxivid, version))


def demo():
    tok = CoreNLPTokenizer()

    examples = [
        r"To examine this peculiar feature, we depict [MATH] on the same plot as [MATH] in Fig.(3). It is found that [MATH] coincides with [MATH] at low-[MATH].",
        r"The specific kinetic energy is obtained through the real part (in Fig. 4) of the expression: [EQUATION] On the other hand, the specific flow energy can be evaluated through the real part of the following: [EQUATION] Combining the two, is seen in Fig.(3).",
        r"There are two collapsed halos, A and B, of mass [MATH] and [MATH] respectively, at [MATH] in our simulation as shown in the right panel of Fig.(5).",
        r"There are two collapsed halos (shown in Fig.(5)), A and B, of mass [MATH] and [MATH] respectively, at [MATH] in our simulation as shown in the right panel of Fig.(5).",
        r"Given a Hamiltonian [MATH], one can evolve the wave function through (23). It is simply a unitary transformation of the system, [EQUATION] We use the pseudo-spectral method to solve the Schrodinger equation in the comoving box. Let [MATH] be the kinetic energy operator ([MATH] in Fourier space) and [MATH] the potential operator([MATH] in real space). The evolution is then split into [EQUATION] On the other hand, we need to consider the non-commutative relation between [MATH] and [MATH], where [EQUATION] [EQUATION] It follows that we obtain, to the second order accuracy, [EQUATION] which will be adopted to advance the time steps.",
        r"It is simply a unitary transformation of the system, [EQUATION] We use the pseudo-spectral method to solve the Schrodinger equation in the comoving box.",
        r"In ref.[CITATION] the masses and decay constants of the lightest octet of pseudoscalar mesons are worked out at to [MATH] .",
    ]

    for ex in examples:
        tokens = tok.tokenize(ex)

        for s in tokens.ssplit():
            print(s)
        print()


if __name__ == "__main__":
    main()
    # demo()
