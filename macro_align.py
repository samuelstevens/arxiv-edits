import re
from typing import List, Tuple

CONTENT_PATTERN = re.compile(
    r'\\(?:sub)?section{(.*?)}(.*?)(?=\\(?:sub)?section{.*?})', flags=re.S)


def content(source, title=False):
    match_index = 0 if title else 1
    matches = CONTENT_PATTERN.findall(source)
    return [m[match_index] for m in matches]


def parse_sections(sources: List[str]) -> List[Tuple[str]]:
    # 1. look for \section{.*} and \subsection{.*}
    # 2. when you find one, look for it in the other paper as well
    # 3. set their content equal to each other with the section header as a key

    section_lists = [content(v) for v in sources]

    # rotates the array
    section_tuples = list(zip(*reversed(section_lists)))

    # assume additional sections have not been added or reordered.
    return section_tuples
