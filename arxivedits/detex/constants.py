import re

# $...$
INLINE_MATH_PATTERN = re.compile(r"(?<!\\)\$.*?[^\\]\$", re.MULTILINE | re.DOTALL)

# $$...$$
BLOCK_MATH_PATTERN = re.compile(r"(?<!\\)\$\$.*?[^\\]\$\$", re.MULTILINE | re.DOTALL)

# \section{}, \subsection{}, etc
SECTION_PATTERNS = [
    re.compile(r"\\" + "sub" * i + r"section\*?\{(.*?)\}") for i in range(6)
]

# Tags
MATH_TAG = "[MATH]"
BLOCK_MATH_TAG = "[EQUATION]"
CITE_TAG = "[CITATION]"
REF_TAG = "[REF]"

BAD_TAGS = [
    r"\input",
    r"\author",
    r"\email",
    r"\footnote",
    r"\pacs",
    r"\PACS",
    r"\address",
    r"\setcounter",
    r"\affiliation",
    r"\date",
    r"\label",
    r"\keywords",
    r"\newcounter",
    # extra environments
    r"\begin",
    r"\end",
    r"\tikzset",
    # bibs
    r"bibliographystyle",
    r"bibliography",
]

REF_TAGS = [r"\eqref", r"\ref", r"\autoref", r"\fref"]

CITE_TAGS_REPLACE = [r"\cite", r"\citet"]
CITE_TAGS_REMOVE = [r"\citep", r"\citealt"]
