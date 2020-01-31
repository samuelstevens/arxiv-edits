import string
import logging
import re
from typing import List

from arxivedits.detex import latex

logger = logging.getLogger("delatex")


class FinalContent:
    def __init__(self):
        self.result: List[str] = []

    def appendString(self, text: str):
        self.result.append(text)

    # [CHENHAO] if tokenize then will add space between words
    def appendContent(self, content: str, pos: int, tokenize=False):
        if not tokenize:
            self.result.append(content[pos])
            return

        if (
            content[pos] not in string.ascii_letters
            and content[pos] not in string.digits
            and content[pos] != "-"
        ):
            self.result.append(" %s" % content[pos])
            if pos < len(content) - 1 and content[pos + 1] != " ":
                self.result.append(" ")
        else:
            self.result.append(content[pos])

    def getResult(self) -> str:
        return "".join(self.result)


def getDebt(text: str) -> int:
    """
    Find the number of extra closing (right) braces. Can return a negative number.

    Args:
        text (str):
    """
    debt = 0
    for c in text:
        if c == "{":
            debt -= 1
        elif c == "}":
            debt += 1
    return debt


def removeDefinition(lines: List[str], content: List[str]):
    """
    Removes the following commands from `lines` by keeping track of the stack of `{}`s.

    `def`: `def` lets you define a macro with optional arguments (TeX primitive).

    `newcommand`: `newcommand` lets you define a macro with optional arguments (LaTeX wrapper over `def`).

    `renewcommand`: `renewcommand` lets you redefine a command.

    `newtheorem`: `newtheorem` lets you define custom environments for theorems.

    `setsymbol`: I couldn't find any documentation for `setsymbol`.

    `footmath`: I couldn't find any documentation for `footmath`.

    Args:
        lines (List[str]): list of lines in the orignal LaTeX document.
        content (List[str]): is an empty array that will contain the content.
    """
    debt = 0

    ignoreset = set(
        ["def", "newcommand", "renewcommand", "newtheorem", "setsymbol", "footmath"]
    )
    for line in lines:
        pos = line.find("%")
        # pos != -1 means there is a %
        # (pos - 1 >= 0 and line[pos - 1] == "\\") means that the character before % is \ (escapes the %)
        if pos != -1 and not (pos - 1 >= 0 and line[pos - 1] == "\\"):
            # strips the line to the comment
            line = line[0:pos]

        # if the line is now empty, ignore it.
        if len(line) == 0:
            continue

        # reset position
        pos = 0

        # if the first character in the line is \
        if line[pos] == "\\":
            pos += 1

            # increment pos until we find a non-letter or non-digit char
            while pos < len(line) and (
                line[pos] in string.ascii_letters or line[pos] in string.digits
            ):
                pos += 1

            # we now know that the latex command is some string (bc line[0] is \)
            latexcommand = line[1:pos]

            # if we should ignore this command, set debt to the debt of the line and move to the next line.
            if latexcommand in ignoreset:
                debt = getDebt(line)
                continue

        # if the first character in the line is not \ or it is but the latexcommand should not be ignored...

        # if our current debt is below 0 (we have more left braces than right braces)
        if debt < 0:
            # add the debt of our line
            debt += getDebt(line)

            # if we still have more left braces than right braces, move to next line
            if debt <= 0:
                continue

        # if debt is >= 0, append the line to content.
        content.append("%s\n" % line.strip())


def simpleLatexToText(inputfile: str, outputfile: str, sectioned=False):
    """
    Chenhao's latex to text algorithm.
    """
    fin = open(inputfile)
    lines = fin.readlines()
    fin.close()
    contentlist: List[str] = []
    count = 0

    # remove big commands
    removeDefinition(lines, contentlist)
    content = "".join(contentlist)

    # remove modern math
    content = latex.removeBadMath(content)
    startpos = content.find("\\begin{document}")

    # if you don't see any \begin{document}, don't do anything (return early)
    if startpos == -1:
        logger.warning("no start document %s", inputfile)
        return

    # [CHENHAO] sometimes title appear before document
    titlepos = content.find("\\title")

    # start from the earlier position, either \begin{document} or \title
    if titlepos > 0 and titlepos < startpos:
        startpos = titlepos
    pos = startpos

    # [CHENHAO] label = 'document'
    ignoringmode = set(
        [
            "equation",
            "eqnarray",
            "array",
            "figure",
            "align",
            "table",
            "tabular",
            "math",
            "displaymath",
            "thebibliography",
        ]
    )

    wordpattern = re.compile(r"\w+")
    sectionmode = set(["section", "section*", "title"])
    finalcontent = FinalContent()

    title_end = -2
    while pos < len(content):

        # if we see a \
        if content[pos] == "\\":

            # if we're at \verb
            if content[pos + 1 : pos + 5] == "verb":
                tempInterval = 5
                # accept \verb* as well
                if content[pos + 6] == "*":
                    tempInterval = 6

                tempPos = pos + tempInterval

                # find the position where it is not a space anymore
                while content[tempPos] == " ":
                    tempPos += 1

                # delimiter for our \verb is this first non-space char
                delim = content[tempPos]

                # look for the next occurence of delim in content
                verbEnd = content.find(delim, tempPos + 1)

                # append every character inside the \verb|...|
                for ti in range(tempPos + 1, verbEnd):
                    finalcontent.appendContent(content, ti)
                pos = verbEnd + 1

            # if we're at \ and the next char isn't letter or digit.
            elif (
                content[pos + 1] not in string.ascii_letters
                and content[pos + 1] not in string.digits
            ):
                # if we're at \ (with space)
                if content[pos + 1] == " ":
                    # skip \
                    pos += 1
                else:
                    # skip \ and non letter/digit/space character
                    pos += 2
            else:
                # look past \
                temppos = pos + 1

                # set temppos to the first non-letter/digit char after the \
                while (
                    content[temppos] in string.ascii_letters
                    or content[temppos] in string.digits
                ):
                    temppos += 1

                # latexcommand = text after \
                latexcommand = content[pos + 1 : temppos]
                if latexcommand == "begin":
                    # ignoring mode: equation, eqnarray, array, figure, align, table, tabular
                    modestart = content.find("{", pos)
                    modeend = content.find("}", pos)
                    mode = content[modestart + 1 : modeend]
                    modeword = re.findall(wordpattern, mode)
                    if modeword:
                        tomatchmode = modeword[0]
                    else:
                        tomatchmode = mode
                    if sectioned and tomatchmode == "abstract":
                        finalcontent.appendString("\n###start section abstract###\n")
                    # print tomatchmode
                    if (
                        tomatchmode in ignoringmode
                        or tomatchmode.find("bibliography") != -1
                    ):
                        if content.find("\\end{%s}" % mode, pos + 1) != -1:
                            pos = (
                                content.find("\\end{%s}" % mode, pos + 1)
                                + 6
                                + len(mode)
                            )
                        elif content.find("{%s}" % mode, pos + 1) != -1:
                            pos = content.find("{%s}" % mode, pos + 1) + 2 + len(mode)
                        else:
                            pos = modeend + 1
                    else:
                        pos = modeend + 1
                elif latexcommand == "end":
                    modestart = content.find("{", pos)
                    if modestart != -1:
                        modeend = content.find("}", pos)
                        pos = modeend + 1
                        if sectioned:
                            mode = content[modestart + 1 : modeend].lower()
                            if mode.strip() == "abstract":
                                finalcontent.appendString(
                                    "\n###start dummy section###\n"
                                )
                    else:
                        pos += 1
                elif sectioned and latexcommand in sectionmode:
                    modestart = 0
                    if content[temppos] == "[":
                        temp = content.find("]", pos)
                        modestart = content.find("{", temp)
                    else:
                        modestart = content.find("{", pos)
                    pastparenthsis = 0
                    modeend = modestart
                    # find matching parathesis
                    while True:
                        modeend += 1
                        if content[modeend] == "}":
                            pastparenthsis -= 1
                            if pastparenthsis < 0:
                                break
                        elif content[modeend] == "{":
                            pastparenthsis += 1
                    mode = "".join(
                        [
                            "%s " % a.strip()
                            for a in content[modestart + 1 : modeend].splitlines()
                        ]
                    )
                    if latexcommand == "title":
                        finalcontent.appendString("\n###start section title###\n")
                        title_end = modeend
                    else:
                        finalcontent.appendString("\n###start section %s###\n" % mode)
                    pos = temppos
                else:
                    pos = temppos
        elif content[pos] == "$":
            if content[pos + 1] == "$":
                endpos = pos
                while True:
                    endpos = content.find("$$", endpos + 2)
                    if content[endpos - 1] != "\\" or (
                        content[endpos - 1] == "\\" and content[endpos - 2] == "\\"
                    ):
                        break
                    else:
                        endpos -= 1
                pos = endpos + 2
            else:
                endpos = pos
                while True:
                    endpos = content.find("$", endpos + 1)
                    if content[endpos - 1] != "\\" or (
                        content[endpos - 1] == "\\" and content[endpos - 2] == "\\"
                    ):
                        break
                pos = endpos + 1
        else:
            finalcontent.appendContent(content, pos)
            if sectioned and pos == title_end + 1:
                logger.info(
                    "title found %s %d %s", inputfile, title_end, content[title_end + 1]
                )
                finalcontent.appendString("\n###start section dummy###\n")
            pos += 1
        if pos < count:
            logger.error(
                "find error %s %s %d %d %d",
                inputfile,
                content[(count - 100) : count],
                count,
                len(content),
                pos,
            )
            break
        else:
            count = pos
    fout = open(outputfile, "w")
    lines = finalcontent.getResult().split("\n")
    logger.info("line number %d", len(lines))
    linenum = 0
    percent = 0.8
    for line in lines:
        linenum += 1
        if line.find("References") != -1 and linenum > percent * len(lines):
            break
        line = line.strip()
        words = line.split()
        for word in words:

            fout.write("%s " % word)
        if line:
            fout.write("\n")
    fout.close()
