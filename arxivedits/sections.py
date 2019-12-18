'''
Takes LaTeX source files and parses the sections. Writes the sections to data/sections.

data/unzipped -> data/sections
'''


import os
import json
import re
from typing import List
from collections import namedtuple


# custom types
Section = namedtuple('Section', 'title text')


def clean_text(text: str) -> str:
    '''
    Strips whitespace and turns 1+ whitespace characters into a single space.
    '''
    text = text.strip()

    whitespacepattern = re.compile(r'\s+')

    return whitespacepattern.sub(' ', text)


def parsesections(textfilepath: str) -> List[Section]:
    '''
    Parses a markdown text file and returns a list of tuples of
    (section name, )
    '''

    titlepattern = re.compile(r'^# (.*)', re.MULTILINE)

    with open(textfilepath, 'r') as file:
        markdowntext = file.read().replace('\u00a0', ' ')

    title = titlepattern.search(markdowntext, 0)
    intialtitle = '### Initial Section (MANUAL) ###'

    # if there are no matches, then the entire file goes in a single json object.
    if not title:
        print(f'Only one section found in {textfilepath}')
        return [Section(title=intialtitle, text=clean_text(markdowntext))]

    text = markdowntext[0:title.span()[0]]
    sections = [Section(title=intialtitle, text=clean_text(text))]

    # if you have a match, you need to find another further match and pick the text out.
    while title:
        nexttitle = titlepattern.search(markdowntext, title.span()[1])
        if not nexttitle:
            # reached end of file. Put the rest of the text in the section and call it a day
            text = markdowntext[title.span()[1]:]
            sections.append(Section(title=title[1], text=clean_text(text)))
            break

        text = markdowntext[title.span()[1]:nexttitle.span()[0]]
        sections.append(Section(title=title[1], text=clean_text(text)))
        title = nexttitle

    return sections


def main():
    '''
    For every file in data/text, take the sections out and write it to data/sections as json.
    '''

    textdirectory = os.path.join('data', 'text')
    sectionsdirectory = os.path.join('data', 'sections')

    if not os.path.isdir(sectionsdirectory):
        os.mkdir(sectionsdirectory)

    for textfile in os.listdir(textdirectory):
        textfilepath = os.path.join(textdirectory, textfile)

        sections = parsesections(textfilepath)

        sectionsfilepath = os.path.join(
            sectionsdirectory, f'{textfile}.json')

        with open(sectionsfilepath, 'w') as file:
            json.dump(sections, file, indent=2)


if __name__ == '__main__':
    main()
