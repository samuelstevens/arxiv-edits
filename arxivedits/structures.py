# built in
from typing import Tuple, NewType

# external
from oaipmh.common import Metadata, Header


Record = Tuple[Header, Metadata, None]
ArxivID = NewType('ArxivID', str)
