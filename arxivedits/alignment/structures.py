from typing import List, Set
from dataclasses import dataclass
from enum import Enum

from arxivedits.alignment.sentence import SentenceID

STATUS = Enum("STATUS", ["UNKNOWN", "SOLVED", "USED", "BORING"])


# data structures needed
@dataclass
class DiffStruct:
    code: int
    sentence: str


@dataclass
class SentenceStruct:
    index: int
    identifiers: List[SentenceID]  # an unchanged sentence has two identifiers
    diff: DiffStruct
    status: STATUS
    aligned: Set[int]  # list of indices
