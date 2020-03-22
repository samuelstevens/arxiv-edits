"""
Exports 3 methods of extracting text from a file: `opendetex` + preprocessing, `pandoc` + postprocessing, and Chenhao Tan's Python solution.
"""

from arxivedits.detex.opendetex import detex_file
from arxivedits.detex.pandoc import pandoc_file
from arxivedits.detex.chenhao import simpleLatexToText as chenhao_file  # type: ignore

# public methods
# detex_file
# pandoc_file
# chenhao_file

# everything else must be accessed manually (only for testing purposes)
