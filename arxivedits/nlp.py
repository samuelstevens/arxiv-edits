'''
Exposes `ArxivTokenizer`, a sentence and word tokenizer with several hand-coded rules specific to Arxiv/LaTeX documents.
'''

from typing import List, Set
from functools import reduce

import nltk.data
from nltk.tokenize.treebank import TreebankWordTokenizer


class ArxivTokenizer:
    '''
    A sentence and word tokenizer with several hand-coded rules specific to Arxiv/LaTeX documents.
    '''

    def __init__(self):
        self.detector = nltk.data.load('tokenizers/punkt/english.pickle')
        self.false_split_suffixes: Set[str] = set(
            ['Fig.', 'Sec.', 'Ref.', 'Figs.', 'Secs.'])
        self.tokenizer = TreebankWordTokenizer()
        # might want to use /\d+\w+\./ as a regex match for references that cause splitting as well, but only if the next letter is lowercase.

    def __split_sent(self, text: str) -> List[str]:
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

    def __split_word(self, sentence: str) -> List[str]:
        '''
        Splits a sentence into words.
        '''
        return self.tokenizer.tokenize(sentence)

    def split(self, text: str, group='') -> List[str]:
        '''
        Splits text into either sentences or words.
        '''
        if group == 'sentence':
            return self.__split_sent(text)
        if group == 'word':
            return self.__split_word(text)

        raise ValueError("group must be either 'sentence' or 'word'.")
