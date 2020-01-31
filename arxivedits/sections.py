"""
Takes LaTeX source files and parses the sections. Writes the sections to data/sections.

data/unzipped -> data/sections
"""


import os
import json
import re
import heapq
from typing import List, Tuple
from collections import namedtuple

import Levenshtein


from data import SECTIONS_DIR, is_x
import structures
from structures import Title, Score, Content


# custom types
Section = namedtuple("Section", "title text")
SectionPair = Tuple[Score, Tuple[Title, Title], Tuple[Content, Content]]


def cleant(text: str) -> str:
    """
    Strips whitespace and turns 1+ whitespace characters into a single space.
    """
    text = text.strip()

    whitespacepattern = re.compile(r"\s+")

    return whitespacepattern.sub(" ", text)


def parsesections(textfilepath: str) -> List[Section]:
    """
    Parses a markdown text file and returns a list of tuples of
    (section name, )
    """

    titlepattern = re.compile(r"^# (.*)", re.MULTILINE)

    subtitlepattern = re.compile(r"^(##+ .*)", re.MULTILINE)

    with open(textfilepath, "r") as file:
        markdowntext = file.read().replace("\u00a0", " ")

    markdowntext = subtitlepattern.sub("", markdowntext)

    title = titlepattern.search(markdowntext, 0)
    intialtitle = "### Initial Section (MANUAL) ###"

    # if there are no matches, then the entire file goes in a single json object.
    if not title:
        # print(f'Only one section found in {textfilepath}')
        return [Section(title=intialtitle, text=cleant(markdowntext))]

    text = markdowntext[0 : title.span()[0]]

    sections: List[Section] = []

    if text:
        sections.append(Section(title=intialtitle, text=cleant(text)))

    # if you have a match, you need to find another further match and pick the text out.
    while title:
        nexttitle = titlepattern.search(markdowntext, title.span()[1])
        if not nexttitle:
            # reached end of file. Put the rest of the text in the section and call it a day
            text = markdowntext[title.span()[1] :]
            sections.append(Section(title=title[1], text=cleant(text)))
            break

        text = markdowntext[title.span()[1] : nexttitle.span()[0]]
        sections.append(Section(title=title[1], text=cleant(text)))
        title = nexttitle

    return sections


def is_sectioned(arxivid, versioncount) -> bool:
    return is_x(arxivid, versioncount, SECTIONS_DIR, extension=".json")


def align(
    v1: List[structures.Section], v2: List[structures.Section]
) -> List[SectionPair]:

    sortedpairs: List[SectionPair] = []

    for v1title, v1content in v1:
        for v2title, v2content in v2:
            score: Score = Score(Levenshtein.distance(v1title, v2title))
            possiblesectionpair: SectionPair = (
                score,
                (v1title, v2title),
                (v1content, v2content),
            )
            heapq.heappush(sortedpairs, possiblesectionpair)

    v1availabletitles = {title for title, _ in v1}
    v2availabletitles = {title for title, _ in v2}

    matchedsections: List[SectionPair] = []

    while len(matchedsections) < max(len(v1), len(v2)):
        nextsection = heapq.heappop(sortedpairs)
        score, titles, _ = nextsection

        v1title, v2title = titles

        if v1title not in v1availabletitles and v2title not in v2availabletitles:
            continue

        if v1title in v1availabletitles:
            v1availabletitles.remove(v1title)

        if v2title in v2availabletitles:
            v2availabletitles.remove(v2title)

        matchedsections.append(nextsection)

    return matchedsections


def main():
    """
    For every file in data/text, take the sections out and write it to data/sections as json.
    """

    if not os.path.isdir(SECTIONS_DIR):
        os.mkdir(SECTIONS_DIR)

    for textfile in os.listdir(TEXT_DIR):
        textfilepath = os.path.join(TEXT_DIR, textfile)

        sections = parsesections(textfilepath)

        sectionsfilepath = os.path.join(SECTIONS_DIR, f"{textfile}.json")

        with open(sectionsfilepath, "w") as file:
            json.dump(sections, file, indent=2)


if __name__ == "__main__":
    main()
