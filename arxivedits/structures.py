"""
Various types used in this application.
"""

# built in
from typing import Tuple, List, NewType, Union, TypeVar, Optional

# external
from oaipmh.common import Metadata, Header  # type: ignore

T = TypeVar("T")
Res = Union[T, Exception]

# just like Go's value, err combos.
Go = Tuple[T, Optional[Exception]]
# I find Go useful when I want a function to return an error, but sometimes I want to ignore the error. With Res, I have to pattern match (can't ignore the error). Maybe later, I'll decide that being forced to handle the error is important.

Record = Tuple[Header, Metadata, None]
ArxivID = NewType("ArxivID", str)


# class ArxivID:
#     def __init__(self, arxivid: str):
#         self.arxivid = arxivid


Title = NewType("Title", str)
Sentence = NewType("Sentence", str)
Content = List[Sentence]
Score = NewType("Score", float)
Section = Tuple[Title, Content]

