# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
'''
Base tokenizer/tokens classes and utilities.
'''

from functools import reduce
from typing import List
import json
import copy
import os
import re
import pathlib

import pexpect

# from nltk.tokenize.treebank import TreebankWordTokenizer
from nltk import word_tokenize
import nltk.data

from data import SENTENCES_DIR, SECTIONS_DIR

FALSE_SPLIT_SUFFIXES = set(
    ['Fig.', 'Sec.', 'Ref.', 'Figs.', 'Secs.', 'Refs.'])


class Tokens():
    '''
    A class to represent a list of tokenized text.
    '''

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

    def __len__(self):
        '''
        The number of tokens.
        '''
        return len(self.data)

    def slice(self, i=None, j=None):
        '''
        Return a view of the list of tokens from [i, j).
        '''
        new_tokens = copy.copy(self)
        new_tokens.data = self.data[i: j]
        return new_tokens

    def ssplit(self):
        sentence_list = []
        original_sentence = self.untokenize()
        dict_a = self.output

        for sentence in dict_a['sentences']:
            start_offset = sentence['tokens'][0]['characterOffsetBegin']
            end_offset = sentence['tokens'][-1]['characterOffsetEnd']
            sentence_list.append(
                original_sentence[start_offset:end_offset+1].strip())

        def join_sentences(sentences: List[str], newsentence: str) -> List[str]:
            if not sentences:
                return [newsentence]

            last_sentence = sentences[-1]

            for suf in self.false_split_suffixes:
                if last_sentence.endswith(suf):
                    sentences[-1] = last_sentence + ' ' + newsentence
                    return sentences

            return sentences + [newsentence]

        return reduce(join_sentences, sentence_list, [])

    def untokenize(self):
        '''
        Returns the original text (with whitespace reinserted).
        '''
        return ''.join([t[self.TEXT_WS] for t in self.data]).strip()

    def words(self, uncased=False):
        '''
        Returns a list of the text of each token

        Args:
            uncased: lower cased text
        '''
        if uncased:
            return [t[self.TEXT].lower() for t in self.data]

        return [t[self.TEXT] for t in self.data]

    def offsets(self):
        '''
        Returns a list of [start, end) character offsets of each token.
        '''
        return [t[self.SPAN] for t in self.data]

    def pos(self):
        '''
        Returns a list of part-of-speech tags of each token.
        Returns None if this annotation was not included.
        '''
        if 'pos' not in self.annotators:
            return None
        return [t[self.POS] for t in self.data]

    def lemmas(self):
        '''
        Returns a list of the lemmatized text of each token.
        Returns None if this annotation was not included.
        '''
        if 'lemma' not in self.annotators:
            return None
        return [t[self.LEMMA] for t in self.data]

    def entities(self):
        '''
        Returns a list of named-entity-recognition tags of each token.
        Returns None if this annotation was not included.
        '''
        if 'ner' not in self.annotators:
            return None
        return [t[self.NER] for t in self.data]

    def ngrams(self, n=1, uncased=False, filter_fn=None, as_strings=True):
        '''
        Returns a list of all ngrams from length 1 to n.

        Args:
            n: upper limit of ngram length
            uncased: lower cases text
            filter_fn: user function that takes in an ngram list and returns
              True or False to keep or not keep the ngram
            as_string: return the ngram as a string vs list
        '''
        def _skip(gram):
            if not filter_fn:
                return False
            return filter_fn(gram)

        words = self.words(uncased)
        ngrams = [(s, e + 1)
                  for s in range(len(words))
                  for e in range(s, min(s + n, len(words)))
                  if not _skip(words[s:e + 1])]

        # Concatenate into strings
        if as_strings:
            ngrams = ['{}'.format(' '.join(words[s:e])) for (s, e) in ngrams]

        return ngrams

    def entity_groups(self):
        '''
        Group consecutive entity tokens with the same NER tag.
        '''

        entities = self.entities()
        if not entities:
            return None
        non_ent = self.opts.get('non_ent', 'O')
        groups = []
        idx = 0
        while idx < len(entities):
            ner_tag = entities[idx]
            # Check for entity tag
            if ner_tag != non_ent:
                # Chomp the sequence
                start = idx
                while (idx < len(entities) and entities[idx] == ner_tag):
                    idx += 1
                groups.append((self.slice(start, idx).untokenize(), ner_tag))
            else:
                idx += 1
        return groups


class Tokenizer():
    '''
    Base tokenizer class.
    Tokenizers implement tokenize, which should return a Tokens class.
    '''

    def tokenize(self, text) -> Tokens:
        raise NotImplementedError

    def shutdown(self):
        pass

    def __del__(self):
        self.shutdown()


class CoreNLPTokenizer(Tokenizer):
    '''
    Simple wrapper around the Stanford CoreNLP pipeline.

    Serves commands to a java subprocess running the jar. Requires Java 8.

    Written by Chao Jiang
    '''

    def __init__(self, **kwargs):
        '''
        Args:
            annotators: set that can include pos, lemma, and ner.
            classpath: Path to the corenlp directory of jars
            mem: Java heap memory
        '''

        self.classpath = '/Users/samstevens/Java/stanford-corenlp/*'
        self.annotators = copy.deepcopy(kwargs.get('annotators', set()))
        self.mem = kwargs.get('mem', '2g')

        with open(os.path.join(pathlib.Path(__file__).parent, 'data', 'latex-unicode.json'), 'r') as file:
            self.latex = json.load(file)

        self._launch()

    def _launch(self):
        '''
        Start the CoreNLP jar with pexpect.
        '''

        annotators = ['tokenize', 'ssplit']
        if 'ner' in self.annotators:
            annotators.extend(['pos', 'lemma', 'ner'])
        elif 'lemma' in self.annotators:
            annotators.extend(['pos', 'lemma'])
        elif 'pos' in self.annotators:
            annotators.extend(['pos'])
        annotators = ','.join(annotators)
        options = ','.join(['untokenizable=noneDelete',
                            'invertible=true'])
        cmd = ['java', '-mx' + self.mem, '-cp', f'"{self.classpath}"', 'edu.stanford.nlp.pipeline.StanfordCoreNLP',
               '-annotators', annotators, '-tokenize.options', options, '-outputFormat', 'json', '-prettyPrint', 'false']

        # We use pexpect to keep the subprocess alive and feed it commands.
        # Because we don't want to get hit by the max terminal buffer size,
        # we turn off canonical input processing to have unlimited bytes.
        self.corenlp = pexpect.spawn('/bin/bash', maxread=100000, timeout=60)
        self.corenlp.setecho(False)
        self.corenlp.sendline('stty -icanon')
        self.corenlp.sendline(' '.join(cmd))
        self.corenlp.delaybeforesend = 0
        self.corenlp.delayafterread = 0
        self.corenlp.expect_exact('NLP>', searchwindowsize=100)

    @staticmethod
    def _convert(token):
        if token == '-LRB-':
            return '('
        if token == '-RRB-':
            return ')'
        if token == '-LSB-':
            return '['
        if token == '-RSB-':
            return ']'
        if token == '-LCB-':
            return '{'
        if token == '-RCB-':
            return '}'
        return token

    def _process(self, text: str) -> str:
        '''
        Takes text and removes block math ($$...$$) and tries to reduce inline math ($...$) as much as possible.
        '''
        text = text.replace('\n', ' ')

        blockpattern = re.compile(r'\$\$(.*)\$\$')
        text = blockpattern.sub('', text)

        inlinepattern = re.compile(r'\$(.*?)\$')

        output = ''
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
        if 'NLP>' in text:
            raise RuntimeError('Bad token (NLP>) in text!')

        # Sending q will cause the process to quit -- manually override
        if text.lower().strip() == 'q':
            token = text.strip()
            index = text.index(token)
            data = [(token, text[index:], (index, index + 1), 'NN', 'q', 'O')]
            return Tokens(data, self.annotators)

        # Minor cleanup before tokenizing.
        clean_text = self._process(text)

        self.corenlp.sendline(clean_text.encode('utf-8'))
        self.corenlp.expect_exact('NLP>', searchwindowsize=100)

        # Skip to start of output (may have been stderr logging messages)
        output = self.corenlp.before
        start = output.find(b'{\r\n  "sentences":')
        output = json.loads(output[start:].decode('utf-8'))

        data = []
        tokens = [t for s in output['sentences'] for t in s['tokens']]
        # print(output)
        for i, _ in enumerate(tokens):
            # Get whitespace
            start_ws = tokens[i]['characterOffsetBegin']
            if i + 1 < len(tokens):
                end_ws = tokens[i + 1]['characterOffsetBegin']
            else:
                end_ws = tokens[i]['characterOffsetEnd']

            data.append((
                self._convert(tokens[i]['word']),
                clean_text[start_ws: end_ws],
                (tokens[i]['characterOffsetBegin'],
                 tokens[i]['characterOffsetEnd']),
                tokens[i].get('pos', None),
                tokens[i].get('lemma', None),
                tokens[i].get('ner', None)
            ))
        return Tokens(data, self.annotators, output=output)


class ArxivTokenizer:
    '''
    A sentence and word tokenizer with several hand-coded rules specific to Arxiv/LaTeX documents.
    '''

    def __init__(self, annotators=None):
        self.detector = nltk.data.load('tokenizers/punkt/english.pickle')

        # might want to use /\d+\w+\./ as a regex match for references that cause splitting as well, but only if the next letter is lowercase.
        self.false_split_suffixes = FALSE_SPLIT_SUFFIXES

        self.annotators = annotators or set()

    def __split_sent(self, text: str) -> List[str]:
        split = self.detector.tokenize(text.replace('\n', ' '))

        def join_sentences(sentences: List[str], newsentence: str) -> List[str]:
            if not sentences:
                return [newsentence]

            lastsentence = sentences[-1]

            for suf in self.false_split_suffixes:
                if lastsentence.endswith(suf):
                    sentences[-1] = lastsentence + ' ' + newsentence
                    return sentences

            return sentences + [newsentence]

        return reduce(join_sentences, split, [])

    def __split_word(self, sentence: str) -> List[str]:
        '''
        Splits a sentence into words.
        '''
        return word_tokenize(sentence)

    def split(self, text: str, group='') -> List[str]:
        '''
        Splits text by either 'sentence' or 'word'.
        '''
        if group == 'sentence':
            return self.__split_sent(text)
        if group == 'word':
            return self.__split_word(text)

        raise ValueError("group must be either 'sentence' or 'word'.")


def main():
    '''
    Loads sections from data/sections and sends them to data/sentences
    '''
    tok = CoreNLPTokenizer()
    # tok = ArxivTokenizer()

    if not os.path.isdir(SENTENCES_DIR):
        os.mkdir(SENTENCES_DIR)

    for sectionfile in os.listdir(SECTIONS_DIR):

        sectionfilepath = os.path.join(SECTIONS_DIR, sectionfile)

        with open(sectionfilepath, 'r') as file:
            sections = json.load(file)

        sentencelist = []

        for section in sections:
            title, text = section
            # this step is quite important, in the original sent, there is \xa0 that looks like a white space
            text = " ".join(text.split())

            try:
                sentences = tok.tokenize(text).ssplit()
                # sentences = tok.split(text, group='sentence')
            except json.decoder.JSONDecodeError as err:
                print(err.msg)
                print(f'Error with {sectionfilepath} in {title}')
            else:
                sentencelist.append([title, sentences])

        sectionfile, _ = os.path.splitext(sectionfile)

        sentencesfilepath = os.path.join(
            SENTENCES_DIR, f'{sectionfile}.json')

        with open(sentencesfilepath, 'w') as file:
            json.dump(sentencelist, file, indent=2)


def demo():
    tok = CoreNLPTokenizer()

    tokens = tok.tokenize(
        r'Similarly, it can be observed from Fig. [\[fig:SF\_PS\_alpha\]](#fig:SF_PS_alpha){reference-type="ref" reference="fig:SF_PS_alpha"} that for the PSR protocol, throughput increases as $\rho$ increases from $0$ to some optimal $\rho$ ($0.63$ for $\sigma^2_{n_a}= 0.01$) but later, it starts decreasing as $\rho$ increases from its optimal value.')

    for s in tokens.ssplit():
        print(s)


if __name__ == '__main__':
    # main()
    demo()
