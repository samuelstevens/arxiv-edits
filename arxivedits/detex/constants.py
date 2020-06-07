import re

# \section{}, \subsection{}, etc
SECTION_PATTERNS = [
    re.compile(r"\\" + "sub" * i + r"section\*?\{(.*?)\}", re.DOTALL) for i in range(6)
]

ACKNOWLEDGEMENT_PATTERN = re.compile(r"#* ?Acknowledge?ments?\.?")

# Tags
INLINE_MATH_TAG = "[MATH]"
BLOCK_MATH_TAG = "[EQUATION]"
CITE_TAG = "[CITATION]"
REF_TAG = "[REF]"

BAD_TAGS = [
    r"\input",
    # authors
    r"\author",
    r"\authors",
    r"\correspondingauthor",
    r"authorrunning",
    r"\email",
    r"\offprints",
    r"\footnote",
    r"\foot",
    r"\pacs",
    r"\PACS",
    r"\address",
    r"\setcounter",
    r"\affiliation",
    r"\institute",
    r"\date",
    r"\label",
    r"\keywords",
    r"\newcounter",
    r"\urladdr",
    r"\thispagestyle",  # hep-ph-98013990-v1
    r"\footnotetext",
    # extra environments
    r"\begin",
    r"\end",
    r"\tikzset",
    # bibs
    r"bibliographystyle",
    r"bibliography",
    r"\textcolor",
]

REF_TAGS = [r"\eqref", r"\ref", r"\autoref", r"\fref", r"\lref", r"\eqref", r"\refs"]

CITE_TAGS_REPLACE = [r"\cite", r"\citet"]
CITE_TAGS_REMOVE = [r"\citep", r"\citealt", r"\nocite"]
