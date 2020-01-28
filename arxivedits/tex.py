import subprocess
import string
import re
import os
from typing import Optional, List, Tuple, Dict

import logging

from data import TEXT_DIR, UNZIPPED_DIR, is_x
from structures import Res

logger = logging.getLogger("delatex")

# regex patterns

# \somecommand%\n
MACRO_COMMENT_PATTERN = re.compile(r"\w%$")

# \citet{...}
EXTRACT_CITATION_PATTERN = re.compile(r"\\citet\[?.*?\]?\{.*?\}")

# \includegraphics{...}, \includegraphics[...]{...}
GRAPHICS_PATTERN = re.compile(
    r"\\includegraphics(:?\[.*?\])?\{.*?\}", re.MULTILINE | re.DOTALL
)

SECTION_PATTERNS = [
    re.compile(r"\\" + "sub" * i + r"section\{(.*?)\}") for i in range(6)
]

BAD_TAGS = [
    "cite",
    "citep",
    "citealt",
    "input",
    "author",
    "email",
    "footnote",
    "pacs",
    "address",
    "setcounter"
]

# $...$
INLINE_MATH_PATTERN = re.compile(r"(?<!\\)\$.*?[^\\]\$", re.MULTILINE | re.DOTALL)

# $$...$$
BLOCK_MATH_PATTERN = re.compile(r"(?<!\\)\$\$.*?[^\\]\$\$", re.MULTILINE | re.DOTALL)


# Tags
MATH_TAG = "[MATH]"
BLOCK_MATH_TAG = "[EQUATION]"
CITE_TAG = "[CITATION]"


def pandoc_file(
    inputfile, outputfile, to="markdown", clean=True
) -> Optional[Exception]:
    with open(inputfile, "r") as file:
        content = file.read()

    if clean:
        content = clean_tex(content, basic=True)

    try:
        result = subprocess.run(
            [
                "pandoc",
                "--from",
                "latex",
                "--to",
                to,
                "--standalone",
                "--atx-headers",
                "--output",
                outputfile,
            ],
            input=content,
            text=True,
            timeout=5,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        return Exception(f"Timed out on {inputfile}")
    else:
        if result and result.returncode != 0:
            print(result.stderr)
            return Exception(f"Error with {inputfile}")
        return None


def detex_file(inputfile, outputfile, clean=True):

    mathtag = "[MATH]"
    verbtag = "[DOES]"
    nountag = "[NOUN]"

    with open(inputfile, "r") as fin:
        with open(outputfile, "w") as fout:
            content = fin.read()

            content = content.replace("noun", nountag)

            if clean:
                content = clean_tex(content)

            output = detex(content)

            output = output.replace("noun", mathtag)
            output = output.replace("verbs", verbtag)
            output = output.replace(nountag, "noun")

            fout.write(output)


def detex(text: str) -> str:
    """
    opendetex (https://github.com/pkubowicz/opendetex), installed via homebrew (brew install detex)
    """

    try:
        result = subprocess.run(
            ["detex", "-r"], text=True, input=text, capture_output=True
        )
        return result.stdout
    except AttributeError:
        print(
            f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes)."
        )
        return ""


def find_pair(
    opening_char: str, closing_char: str, text: str, start: int = 0
) -> Res[int]:
    """
    Takes a pair of characters and text and finds the location of the ending char.

    `"{ {} }"` would return the location of the second `'}'`.
    """
    # go to first start_char
    pos = text.find(opening_char, start)

    if pos < 0:
        return ValueError(f"substring {opening_char} not found.")

    if opening_char == closing_char:
        pos = text.find(opening_char, pos + 1)

        if pos < 0:
            return ValueError(f"No matching {closing_char}.")

        return pos

    count = 0

    while pos < len(text):
        if text[pos] == opening_char:
            count += 1
        elif text[pos] == closing_char:
            count -= 1

        if count == 0:
            return pos

        pos += 1

    return ValueError(f"No matching {closing_char}.")


def clean_tex(initial_tex: str, basic=False) -> str:
    """
    Preprocesses a LaTeX file for use with `opendetex` or `pandoc` (in plaintext format)

    Args:
        initial_tex (str): LaTeX file as a string.
        basic (bool): if True, clean_tex will not preprocess macros or other advanced cleaning. When using pandoc, set basic to True.
    """
    lines = initial_tex.split("\n")

    # removes comments
    lines = [line for line in lines if not line.lstrip().startswith("%")]

    # joins all lines that end with <non-whitespace>%
    i = 0
    while i < len(lines):
        if MACRO_COMMENT_PATTERN.search(lines[i]):
            lines[i] = lines[i][:-1]
            lines[i] += lines[i + 1]
            lines[i + 1] = ""
            i += 1

        i += 1

    # removes lines with \authorblock
    lines = [line for line in lines if not line.lstrip().startswith(r"\authorblock")]

    text = "\n".join(lines)

    # changes \citet{something} to [CITATION]
    text = EXTRACT_CITATION_PATTERN.sub(CITE_TAG, text)

    text = GRAPHICS_PATTERN.sub("", text)

    text = remove_environments(text)

    bad_tags = ["\\" + t for t in BAD_TAGS]

    for tag in bad_tags:
        text = remove_tag(tag, text)

    text = remove_tag(r"\input", text, braces=[" ", " "])

    if not basic:
        # remove \label{...}
        text = remove_tag(r"\label", text)

        # changes all math to $...$ or $$...$$
        text = removeBadMath(text)

        # change $$...$$ to [EQUATION]
        # needs to go first so that $$...$$ isn't turned to $[MATH]$
        text = BLOCK_MATH_PATTERN.sub(BLOCK_MATH_TAG, text)

        # change $...$ to [MATH]
        text = INLINE_MATH_PATTERN.sub(MATH_TAG, text)

        text = process_macros(text)

        for i, pattern in enumerate(SECTION_PATTERNS):
            text = pattern.sub(r"\\section{" + "#" * (i + 1) + r" \1}\n", text)

    # turns multiple blank lines into one
    text = re.sub(r"\n(\s*\n)+", "\n\n", text)

    # removes blank lines before [EQUATION]
    regexp = r"\n\n+\[EQUATION\]"
    text = re.sub(regexp, f"\n{BLOCK_MATH_TAG}", text)

    # removes blank lines after [EQUATION]
    regexp = r"\[EQUATION\]( ?\n)( ?\n)+"
    text = re.sub(regexp, f"{BLOCK_MATH_TAG}\n", text)

    start_doc = text.find(r"\begin{document}")

    if start_doc >= 0:
        text = text[start_doc:]

    # removes multiple spaces
    text = re.sub(r" +", " ", text, flags=re.MULTILINE)

    # removes spaces at the start of a line
    text = re.sub("^ ", "", text, flags=re.MULTILINE)

    return text


def line_starts_with(search: str, text: str, position: int) -> bool:
    if position < 0:
        position = 0
    if position > len(text) - len(search):
        position = len(text) - len(search)

    while position >= 0:
        if text[position] == "\n" or text[position] == "\r":
            break

        position -= 1

    # now text[position] is the first char in the line
    position += 1

    return text[position:].startswith(search)


def remove_environments(text: str) -> str:
    """
    Removes bad environments and their contents like `\\begin{equation}` and `\\begin{table}` from text.
    """

    bad_environments = {
        "equation": BLOCK_MATH_TAG,
        "subequation": BLOCK_MATH_TAG,
        "eqnarray": BLOCK_MATH_TAG,
        "array": None,
        "figure": None,
        "align": BLOCK_MATH_TAG,  # same thing as eqnarray
        "table": None,
        "tabular": None,
        "math": MATH_TAG,  # equivalent to $...$
        "matrix": None,
        "displaymath": BLOCK_MATH_TAG,  # equivalent to $$...$$
        "thebibliography": None,
        "keywords": None,  # typically not sentences.
    }

    def get_env_name(subtext: str) -> str:
        r"""
        Assumes subtext starts with `\begins{`
        """
        match = re.match(r"\\begin\{(.*?)\}", subtext)
        if not match:
            logging.warning("Couldn't find \\begin{ in %s", subtext[:20])
            return ""

        return match.group(1)

    valid: List[Tuple[int, int, Optional[str]]] = []

    end_env = 0
    pos = 0
    while pos < len(text):
        start_env = text.find(r"\begin{", pos)

        if start_env < 0:
            valid.append((end_env, len(text), None))
            break

        env_name = get_env_name(text[start_env:])

        if (
            (env_name in bad_environments or env_name[:-1] in bad_environments)
            and not line_starts_with(r"\newcommand", text, start_env)
            and not line_starts_with(r"\def", text, start_env)
        ):  # env_name[:-1] accounts for table*, figure*, etc.

            if env_name in bad_environments:
                replaced = bad_environments[env_name]
            else:
                replaced = bad_environments[env_name[:-1]]

            valid.append((end_env, start_env, replaced))

            end_env_command = r"\end{" + env_name + r"}"

            end_env = text.find(end_env_command, start_env + 1) + len(end_env_command)

            if end_env < 0:
                logger.warning("Missing \\end for %s", end_env_command)
                end_env = len(text)
                break
            pos = end_env
        else:
            pos = start_env + 1  # +1 gets past the initial .find()

    # process valid
    final = []
    for v in valid:
        final.append(text[v[0] : v[1]])
        replacement = v[2]
        if isinstance(replacement, str):
            final.append(replacement)

    return "".join(final)


def remove_tag(tag: str, text: str, braces=["{", "}"]) -> str:
    """
    Removes tags like `\\footnote` or `\\def` from a string by using `find_pair()` to handle nested braces. This is better than guessing if a greedy regex will work.
    """

    tags_with_extra_braces = [r'\setcounter']

    string_builder: List[str] = []

    end_pos = 0
    current_pos = 0
    tags_found = 0

    while current_pos < len(text):
        start_pos = text.find(tag, current_pos)

        if start_pos < 0:
            string_builder.append(text[end_pos:])
            break

        # if we have the wrong tag, text[start_pos+len(tag)] won't be {, [, etc.
        if text[start_pos + len(tag)] in string.ascii_letters:
            current_pos = start_pos + 1
            continue

        string_builder.append(text[end_pos:start_pos])
        tags_found += 1

        end_of_tag = find_pair(braces[0], braces[1], text, start_pos)

        if isinstance(end_of_tag, Exception):
            print(f"Error in remove tag.")
            print(end_of_tag)
            break

        if tag in tags_with_extra_braces:
            end_of_tag = find_pair(braces[0], braces[1], text, end_of_tag + 1)

        end_pos = end_of_tag + 1  # +1 is for getting past }

        if end_pos >= len(text):
            break

        current_pos = end_pos

    text = "".join(string_builder)

    if tags_found > 0:
        text = re.sub(
            f" ([,. )])", r"\1", text, tags_found
        )  # removes spaces before commas, periods and ).

    return text


def process_macros(initial_tex: str) -> str:
    """
    Copy-pastes commands from `\\newcommand` and `\\def` into their spots.
    """

    # second .* must be greedy
    NEWCOMMAND_PATTERN = re.compile(r"\\(?:re)?newcommand\{(.*?)\}\{(.*)\}")
    DEF_PATTERN = re.compile(r"\\def(\\.*)\{(.*)\}")

    command_lookup: Dict[str, str] = {
        command: output for command, output in NEWCOMMAND_PATTERN.findall(initial_tex)
    }

    def_lookup = {
        command: output for command, output in DEF_PATTERN.findall(initial_tex)
    }

    command_lookup.update(def_lookup)

    text = initial_tex

    # don't allow commands to be used in other commands or defs.
    text = NEWCOMMAND_PATTERN.sub("", text)
    text = DEF_PATTERN.sub("", text)

    for command in command_lookup:
        string_builder = []

        end_command = 0
        pos = 0

        while pos < len(text):
            start_command = text.find(command, pos)

            if start_command < 0:
                # finished with this command
                string_builder.append(text[end_command:])
                break

            # if we find a command, check that it's not escaped with \
            if text[start_command - 1] == "\\":
                pos = start_command + 1
                continue

            string_builder.append(text[end_command:start_command])

            string_builder.append(command_lookup[command])

            end_command = start_command + len(command)

            if end_command >= len(text):
                print(text[start_command:])
                print(command)
                print("UH OH")
                # break

            if (
                text[end_command] not in [".", ",", "-", "}", "{"]
                and text[end_command : end_command + 1] != "{}"
            ):
                end_command += 1

            pos = end_command

        text = "".join(string_builder)

    return text


# Chenhao's code
# START


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


def removeBadMath(content: str) -> str:
    r"""
    Changes modern LaTeX sequences such as `\( \)` and `\[ \]` to `$ $`.
    """
    # result is a list of lines
    result = []
    pos = 0

    while pos < len(content) - 1:
        # if the current 2 chars are \(
        if content[pos : pos + 2] == "\\(":
            # if the previous character was not \ (so the entire sequence is NOT "\\(" )
            if not (pos > 0 and content[pos - 1] == "\\"):
                # add a $ for Latex math
                result.append(" $ ")
                # go past these two chars
                pos += 2
                # start loop again
                continue

        # if the 2 current chars are \(
        if content[pos : pos + 2] == "\\)":
            # making sure the slash isn't escaped
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $ ")
                pos += 2
                continue

        # if the 2 current chars are \[
        if content[pos : pos + 2] == "\\[":
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $$ ")
                pos += 2
                continue

        # if the 2 current chars are \]
        if content[pos : pos + 2] == "\\]":
            if not (pos > 0 and content[pos - 1] == "\\"):
                result.append(" $$ ")
                pos += 2
                continue

        # if this position isn't one of those char sequences, append a single character
        result.append(content[pos])
        pos += 1

    # sometimes you'll end up without the last char.
    if pos < len(content):
        result.append(content[pos])

    # rejoin the string
    return "".join(result)


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
    content = removeBadMath(content)
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


# Chenhao's code
# END


def is_detexed(arxivid, versioncount) -> bool:
    return is_x(arxivid, versioncount, TEXT_DIR)


def main():
    """
    Takes files from data/unzipped and converts them to text, then sends them to data/text.
    """

    error_count = 0

    for sourcefile in os.listdir(UNZIPPED_DIR):
        sourcefilepath = os.path.join(UNZIPPED_DIR, sourcefile)
        outputfilepath = os.path.join(TEXT_DIR, sourcefile)
        err = pandoc_file(sourcefilepath, outputfilepath)

        # detex_file(sourcefilepath, outputfilepath)

        if not os.path.isfile(outputfilepath):
            error_count += 1

        if err:
            print(err)

    print(f"Saw {error_count} errors.")
    print(
        f"{(len(os.listdir(UNZIPPED_DIR)) - error_count) / len(os.listdir(UNZIPPED_DIR)) * 100:.1f}% success."
    )


def demo():
    # print(pandoc_file('data/unzipped/0704.0001-v1',
    #   'data/text/0704.0001-v1'))
    # print(
    #     pandoc_file(
    #         "data/unzipped/1505.04499-v2",
    #         "data/text/1505.04499-v2/pandoc.txt",
    #         to="plain",
    #     )
    # )

    with open("data/unzipped/0806.0232-v2", "r") as infile:
        with open("data/text/0806.0232-v2/clean-tex.tex", "w") as outfile:
            outfile.write(clean_tex(infile.read()))

    with open("data/unzipped/1505.04499-v2", "r") as infile:
        with open("data/text/1505.04499-v2/clean-tex.tex", "w") as outfile:
            outfile.write(clean_tex(infile.read()))

    with open("data/unzipped/cond-mat-0602062-v2", "r") as infile:
        with open("data/text/cond-mat-0602062-v2/clean-tex.tex", "w") as outfile:
            outfile.write(clean_tex(infile.read()))

    # print(
    #     pandoc_file(
    #         "data/unzipped/1505.04499-v2", "data/text/1505.04499-v2/pandoc-updated.md",
    #     )
    # )

    teststrings = [
        r"""
\begin{document}
    \title{hello}

    \begin{abstract}
        This is my abstract (1).

        \begin{table}
            This is my table (1).
        \end{table}
        
        This is my abstract (2).
    \end{abstract}

    This is my document (1).

    \begin{equation}
        This is my equation (1).
    \end{equation}

    \begin{table*}
        This is my table* (1).
    \end{table*}

    This is my document (2).
\end{document}
""",
        r"\begin{document} \begin{abstract} This is my abstract (1). \end{abstract} \end{document}",
        r"""
Despite ELBDM particles in the excited state are with a relativistic temperature, almost all particles are in the ground state and described by a single non-relativistic wave function.

\subsection{Basic Analysis}

The Lagrangian of non-relativistic scalar field in the comoving
frame is
""",
        r"""
In the early stage([MATH]), the stability condition is
governed by the kinetic energy term, where
[MATH] and $dt \leq {{(6 \pi)}^{-1}} (\eta
a^2)$. At the late time, the gravitational potential becomes ever
deeper, and therefore [MATH] is controlled by the potential energy,
where [MATH] is the greatest value of potential in the real
space.
""",
        r"""
We prepare the initial conditions with CMBFAST \citep{cmbfast96} at $z=1000$ with $\Lambda$CDM cosmology.  Such initial conditions differ from that of \citet{hu00},
where the Compton length of ELBDM already has imprints on the power spectrum
at $z=1000$.  We choose this initial condition because only a few low-$k$ modes can grow for our choice of Jean's length and the details of initial power spectrum are irrelevant at the late time.
""",
    ]

    macrotests = [
        r"""
\newcommand{\mdot}{\mbox{M$_{\odot}$ yr$^{-1}$}}
\newcommand{\test}{Hi there!}

\test hello there \mdot\
\\mdot
"""
    ]


if __name__ == "__main__":
    # main()
    # example_detex()

    # print(
    #     detex(
    #         "On the other hand, we have $n_{ch}\sim (m/T) n_+$, and it follows that $T_c\sim(\frac{n_+}{3T})^{1/2}$."
    #     )
    # )

    demo()
