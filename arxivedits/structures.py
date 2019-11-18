'''
Various types used in this application.
'''
# built in
from typing import Tuple, NewType

# external
from oaipmh.common import Metadata, Header


Record = Tuple[Header, Metadata, None]
ArxivID = NewType('ArxivID', str)
