'''
Takes LaTeX source files and parses the sections. Writes the sections to data/sections.
'''


import os
import json
import re
from typing import List, Tuple

# custom types
Section = Tuple[str, str]

UNTITLED_SECTIONS = ['section', 'subsection', 'title']


def parsesections(sourcefilepath) -> List[Section]:
    '''
    Parses a latex source file and returns a list of tuples of
    (section name, original latex source)

    TODO: parse original latex source.
    TODO: implement.
    '''

    # section_pattern = re.compile(
    #     r'\\(title|abstract|section|subsection)\*?(.*?)(?=\\(?:title|abstract|section|subsection))', re.DOTALL)

    section_pattern = re.compile(
        r'[^%]\\(?:(title|abstract|section)\*?|begin\{(abstract)\})(.*?)(?=[^%]\\(?:(?:title|abstract|section)\*?|begin\{abstract\}))', re.DOTALL)  # might want to add |subsection in there

    with open(sourcefilepath, 'r') as file:
        latexsource = file.read()

    sections = section_pattern.findall(latexsource)

    sections = [[section[0], section[2]] if section[0] else [
        section[1], section[2]] for section in sections]

    def extract_section_type(section):
        sectiontype, content = section
        # we want to add the title of the section
        if sectiontype in UNTITLED_SECTIONS and content[0] == '{':
            try:
                endbrace = content.index('}')
            except ValueError:
                endbrace = float('inf')

            try:
                newcommand = content.index('\\')
            except ValueError:
                newcommand = float('inf')

            endpos = min(endbrace, newcommand)
            if endpos < len(content):
                return (sectiontype, content[1:endpos], content[endpos+1:])

            print(
                f'Did not find an ending for {sectiontype} in {sourcefilepath}')

        return (sectiontype, sectiontype, content)

    sections = [extract_section_type(sec) for sec in sections]

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
