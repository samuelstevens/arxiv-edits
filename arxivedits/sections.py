'''
Takes LaTeX source files and parses the sections. Writes the sections to data/sections.

data/unzipped -> data/sections
'''


import os
import json
import re
from typing import List, Tuple

from tex import detex

# custom types
Section = Tuple[str, str]

UNTITLED_SECTIONS = ['section', 'subsection', 'title']


def parsesections(sourcefilepath) -> List[Section]:
    '''
    Parses a latex source file and returns a list of tuples of
    (section name, original latex source)
    '''

    # this regex is causing issues. It creates artifacts like "Approximation for extinction probability of the contact process based on the Gr", "\"obner basis}, which is clearly incorrect.
    section_pattern = re.compile(
        r'[^%]\\(?:(abstract|section)\*?|begin\{(abstract)\})(.*?)(?=[^%]\\(?:(?:abstract|section)\*?|begin\{abstract\}))', re.DOTALL)  # might want to add |subsection in there

    with open(sourcefilepath, 'r') as file:
        latexsource = file.read()

    sections = section_pattern.findall(latexsource)

    sections = [[section[0], section[2]] if section[0] else [
        section[1], section[2]] for section in sections]

    def extract_section_type(section):
        sectiontype, content = section
        # we want to add the title of the section

        # we achive this by looking for {} pairs

        bracecount = 0
        index = 0

        if sectiontype in UNTITLED_SECTIONS:
            while index < 200:
                if content[index] == '{':
                    bracecount += 1

                if content[index] == '}':
                    bracecount -= 1

                if bracecount == 0:
                    return (sectiontype, content[1:index], content[index+1:])

                index += 1

            print(f'Error.')

        return (sectiontype, sectiontype, content)

    sections = [extract_section_type(sec) for sec in sections]

    # This line is causing a lot of problems. The words in detex(c) do not always match the words in data/text
    sections = [(a, b, detex(c)) for a, b, c in sections]

    return sections


def main():
    '''
    For every file in data/unzipped, parse the LaTeX and write it to data/sections as json.
    '''

    unzippeddirectory = os.path.join('data', 'unzipped')
    sectionsdirectory = os.path.join('data', 'sections')

    if not os.path.isdir(sectionsdirectory):
        os.mkdir(sectionsdirectory)

    for sourcefile in os.listdir(unzippeddirectory):
        sourcefilepath = os.path.join(unzippeddirectory, sourcefile)

        sections = parsesections(sourcefilepath)

        sectionsfilepath = os.path.join(
            sectionsdirectory, f'{sourcefile}.json')

        with open(sectionsfilepath, 'w') as file:
            json.dump(sections, file, indent=2)


if __name__ == '__main__':
    main()
