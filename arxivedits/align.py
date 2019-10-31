'''
Tries to align the sentences in two versions of a plain text research paper.
'''

import os
from typing import List, Tuple


def get_sentence_pairs(v1filepath, v2filepath) -> List[Tuple[str, str]]:
    '''
    Returns all the sentence pairs between filepath1 and filepath2. First aligns by sections (title, abstract, introduction, section, subsection). Then aligns using weighted-LCS.

    TODO: find better parameter names
    '''

    with open(v1filepath, 'r') as fin:
        v1source = fin.read()

    with open(v2filepath, 'r') as fin:
        v2source = fin.read()

    print(v1filepath, v2filepath)
    print(len(v1source), len(v2source))

    return []


def main():
    '''
    For every file in data/sections, find its other versions. Then create sentence pairs and write them to data/pairs.
    '''

    textfiles = os.path.join('data', 'section')
    sentencedirectory = os.path.join('data', 'sentences')

    already_seen = set([])

    if not os.path.isdir(sentencedirectory):
        os.mkdir(sentencedirectory)

    for filename in os.listdir(textfiles):
        arxiv_id, version_code = filename.split('-')

        if arxiv_id in already_seen:
            continue

        # assume there are no double digit versions
        version = int(version_code[-1])

        # next version is something like 0704.0002-v2
        nextversionfilepath = os.path.join(
            textfiles, f'{arxiv_id}-v{version + 1}')

        # keep looking for the next version of the paper
        while os.path.isfile(nextversionfilepath):

            # initial version is something like 0704.0002-v1
            currentversionfilepath = os.path.join(
                textfiles, f'{arxiv_id}-v{version}')

            sentencepairs = get_sentence_pairs(
                currentversionfilepath, nextversionfilepath)

            # include both versions in the file name
            sentencefilepath = os.path.join(
                sentencedirectory, f'{arxiv_id}-v{version}-v{version+1}')

            with open(sentencefilepath, 'w') as file:
                # write every sentence pair "sentence", "sentence"
                # TODO: think about escaping " inside the sentences.
                for (sentence1, sentence2) in sentencepairs:
                    file.write(f'"{sentence1}", "{sentence2}"')

            version += 1

            nextversionfilepath = os.path.join(
                textfiles, f'{arxiv_id}-v{version + 1}')

        # only look at an id once
        already_seen.add(arxiv_id)


if __name__ == '__main__':
    main()
