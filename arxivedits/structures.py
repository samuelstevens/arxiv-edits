"""
Various types used in this application.
"""
import os

# built in
from typing import Tuple, List, NewType, Union, TypeVar

# external
from oaipmh.common import Metadata, Header

T = TypeVar("T")
Res = Union[T, Exception]

Record = Tuple[Header, Metadata, None]
ArxivID = NewType("ArxivID", str)

Title = NewType("Title", str)
Sentence = NewType("Sentence", str)
Content = List[Sentence]
Score = NewType("Score", float)
Section = Tuple[Title, Content]

