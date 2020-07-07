"""
Various types used in this application.
"""

import datetime
from dataclasses import dataclass
from typing import Tuple, List, NewType, Union, TypeVar, Optional, Dict, Set

# external
from oaipmh.common import Metadata, Header

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


# just like Go's value, err combinations.
Go = Tuple[T, Optional[Exception]]

# I find Go useful when I want a function to return an error, but sometimes I want to ignore the error. With Res, I have to pattern match (can't ignore the error). Maybe later, I'll decide that being forced to handle the error is important.
Result = Union[T, Exception]


Record = Tuple[Header, Metadata, None]
ArxivID = NewType("ArxivID", str)
ArxivIDPath = NewType("ArxivIDPath", str)

Title = NewType("Title", str)
Sentence = NewType("Sentence", str)
Content = List[Sentence]
Score = NewType("Score", float)
Section = Tuple[Title, Content]


@dataclass
class PaperMetadata:
    arxivid: str
    versions: Dict[int, datetime.datetime]
    categories: Set[str]
    authors: Set[Tuple[str, str]]

    def get_pairs(self) -> List[Tuple[int, int]]:
        result = []
        for arxivid in sorted(self.versions.keys())[:-1]:
            result.append((arxivid, arxivid + 1))

        return result

    def __str__(self) -> str:
        version_str = ", ".join([f"{v}: {self.versions[v]}" for v in self.versions])
        return f"{self.arxivid} ({version_str})"

