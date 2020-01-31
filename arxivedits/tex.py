import subprocess
import string
import re
import csv
import os
from typing import Optional, List, Tuple, Dict


import data
import source
import arxivedits.detex as detex

from structures import Res

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
    "setcounter",
]

# $...$
INLINE_MATH_PATTERN = re.compile(r"(?<!\\)\$.*?[^\\]\$", re.MULTILINE | re.DOTALL)

# $$...$$
BLOCK_MATH_PATTERN = re.compile(r"(?<!\\)\$\$.*?[^\\]\$\$", re.MULTILINE | re.DOTALL)


# Tags
MATH_TAG = "[MATH]"
BLOCK_MATH_TAG = "[EQUATION]"
CITE_TAG = "[CITATION]"


def clean(initial_tex: str, basic=False, macros_processed=False) -> str:
    """
    Preprocesses a LaTeX file for use with `opendetex` or `pandoc` (in plaintext format)

    Args:
        initial_tex (str): LaTeX file as a string.
        basic (bool): if True, clean will not preprocess macros or other advanced cleaning. When using pandoc, set basic to True.
    """
    lines = initial_tex.split("\n")

    # removes comments
    lines = [line for line in lines if not line.lstrip().startswith("%")]

    # remove extra whitespace
    lines = [" ".join(line.split()) for line in lines]

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
        text = detex.removeBadMath(text)

        # change $$...$$ to [EQUATION]
        # needs to go first so that $$...$$ isn't turned to $[MATH]$
        text = BLOCK_MATH_PATTERN.sub(BLOCK_MATH_TAG + " ", text)

        # change $...$ to [MATH]
        text = INLINE_MATH_PATTERN.sub(MATH_TAG + " ", text)

        # do as much work as possible before macros because they are the most fragile.
        if not macros_processed:
            text = detex.process_macros(text)
            # then repeat everything again because macros may have changed stuff.
            text = clean(text, macros_processed=True)

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


def remove_tag(tag: str, text: str, braces=None) -> str:
    """
    Removes tags like `\\footnote` or `\\def` from a string by using `find_pair()` to handle nested braces. This is better than guessing if a greedy regex will work.
    """

    if not braces:
        braces = ["{", "}"]

    tags_with_extra_braces = [r"\setcounter"]

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

        if isinstance(end_of_tag, Exception):
            print(f"Error in remove tag.")
            print(end_of_tag)
            break

        end_pos = end_of_tag + 1  # +1 is for getting past }

        if end_pos >= len(text):
            break

        current_pos = end_pos

    text = "".join(string_builder)

    # I commented this out because Ref.\ ) would turn into Ref.\) and then \) would change to $ (huge issues)
    # if tags_found > 0:
    #     text = re.sub(
    #         f" ([,. )])", r"\1", text, tags_found
    #     )  # removes spaces before commas, periods and ).

    return text


def is_detexed(arxivid: str, version: int) -> bool:
    return os.path.isfile(data.text_path(arxivid, version))


def main():
    """
    Takes .tex files and converts them to text.
    """
    print(len(data.get_local_files()))

    for arxivid, version in [("1906.07111", 2)]:  # data.get_local_files():
        latexfilepath = data.latex_path(arxivid, version)

        if not os.path.isfile(latexfilepath):
            # print(f"{arxivid}-v{version} was not extracted to .tex")
            continue

        outputfilepath = data.text_path(arxivid, version)
        print(latexfilepath)
        detex.detex_file(latexfilepath, outputfilepath)
        print(outputfilepath)
        # outputfilepath = data.clean_latex_path(arxivid, version)
        # with open(latexfilepath, "r") as infile:
        #     with open(outputfilepath, "w") as outfile:
        #         outfile.write(clean(infile.read()))

        # outputfilepath = os.path.join(
        #     data.extrafiles_path(arxivid, version), f"{arxivid}-v{version}-chenhao.txt"
        # )
        # if not os.path.isfile(outputfilepath):
        #     simpleLatexToText(latexfilepath, outputfilepath, sectioned=True)

        # outputfilepath = os.path.join(
        #     data.extrafiles_path(arxivid, version), f"{arxivid}-v{version}-pandoc.md"
        # )
        # if not os.path.isfile(outputfilepath):
        #     pandoc_file(latexfilepath, outputfilepath)


def demo():
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
        \end{document}""",
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
        r"Therefore, despite its overall similarity with the Anderson transition (see also Ref.\ \cite{suppl}), it remains to be seen if this transition can be classified as such.",
    ]

    macrotests = [
        r"""
        \newcommand{\mdot}{\mbox{M$_{\odot}$ yr$^{-1}$}}
        \newcommand{\test}{Hi there!}

        \test hello there \mdot\
        \\mdot
        """
    ]

    for string in teststrings[-1:]:
        print(string)
        print(clean(string))


def script():
    with open(f"{data.DATA_DIR}/matched_sentences.csv") as csvfile:
        reader = csv.reader(csvfile)

        rows = list(reader)

    ids = [row[0] for row in rows]

    localfiles = {
        f"{arxivid}v{v}": (arxivid, v) for arxivid, v in data.get_local_files()
    }

    localfileids = set(localfiles.keys())

    localfiles_from_chenhao = localfileids.intersection(ids)

    localfiles = sorted([localfiles[key] for key in localfiles_from_chenhao])

    print(f"Can inspect {len(localfiles)} localfiles.")

    for arxivid, _ in localfiles:
        if not source.is_downloaded(arxivid, 1):
            source.download_source_files(arxivid, 1)

        if not source.is_extracted(arxivid, 1):
            source.extract_file(
                data.source_path(arxivid, 1), data.latex_path(arxivid, 1)
            )

        if not is_detexed(arxivid, 1):
            detex_file(data.latex_path(arxivid, 1), data.text_path(arxivid, 1))

        version = 2

        if not source.is_downloaded(arxivid, 2):
            source.download_source_files(arxivid, 2)

        if not source.is_extracted(arxivid, 2):
            source.extract_file(
                data.source_path(arxivid, 2), data.latex_path(arxivid, 2)
            )

        if not is_detexed(arxivid, 2):
            detex_file(data.latex_path(arxivid, 2), data.text_path(arxivid, 2))

        print(data.text_path(arxivid, 1))
        print(data.text_path(arxivid, 2))
        print()


if __name__ == "__main__":
    # script()
    main()
    # demo()
    # test()

