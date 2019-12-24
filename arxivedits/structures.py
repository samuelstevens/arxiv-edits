'''
Various types used in this application.
'''
# built in
from typing import Tuple, List, NewType, NamedTuple

# external
from oaipmh.common import Metadata, Header


Record = Tuple[Header, Metadata, None]
ArxivID = NewType('ArxivID', str)

Title = NewType('Title', str)
Sentence = NewType('Sentence', str)
Content = List[Sentence]
Score = NewType('Score', float)
Section = Tuple[Title, Content]
