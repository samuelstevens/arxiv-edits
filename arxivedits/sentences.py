from typing import List, Set
from functools import reduce

import nltk.data
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters


class Splitter:
    def __init__(self):
        self.detector = nltk.data.load('tokenizers/punkt/english.pickle')
        self.false_split_suffixes: Set[str] = set(
            ['Fig.', 'Sec.', 'Ref.', 'Figs.', 'Secs.'])

        # might want to use /\d+\w+\./ as a regex match for references that cause splitting as well, but only if the next letter is lowercase.

    def split(self, text: str) -> List[str]:
        split = self.detector.tokenize(text.replace('\n', ' '))

        def join_sentences(sentences: List[str], new_sentence: str) -> List[str]:
            if not sentences:
                return [new_sentence]

            last_sentence: str = sentences[-1]

            for suf in self.false_split_suffixes:
                if last_sentence.endswith(suf):
                    sentences[-1] = last_sentence + ' ' + new_sentence
                    return sentences

            return sentences + [new_sentence]

        return reduce(join_sentences, split, [])


def main():
    t = Splitter()

    with open('section_example.txt', 'r') as file:
        text = file.read()

    sentences = t.split(text)

    for s in sentences:
        print(s)


if __name__ == '__main__':
    main()
