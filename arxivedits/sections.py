'''
Takes LaTeX source files and parses the sections. Writes the sections to data/sections.
'''


import os
from typing import List, Tuple


Section = Tuple[str, str]


def parsesections(sourcefilepath) -> List[Section]:
    '''
    Parses a latex source file and returns a list of tuples of
    (section name, original latex source)

    TODO: parse original latex source.
    TODO: implement.
    '''

    with open(sourcefilepath, 'r') as file:
        latexsource = file.read()

    return []


def main():
    '''
    For every file in data/unzipped, parse the LaTeX and write it to data/sections with a custom delimiter.
    '''

    unzippeddirectory = os.path.join('data', 'unzipped')
    sectionsdirectory = os.path.join('data', 'sections')

    if not os.path.isdir(sectionsdirectory):
        os.mkdir(sectionsdirectory)

    for sourcefile in os.listdir(unzippeddirectory):
        sourcefilepath = os.path.join(unzippeddirectory, sourcefile)

        sections = parsesections(sourcefilepath)

        sectionsfilepath = os.path.join(sectionsdirectory, sourcefile)

        with open(sectionsfilepath, 'w') as file:
            for section in sections:
                file.write(f"### START SECTION {section['name']} ###")
                file.write(section['body'])
                file.write(f"### END SECTION {section['name']} ###")


if __name__ == '__main__':
    main()
