"""
Exports 3 methods of extracting text from a file: `opendetex` + preprocessing, `pandoc` + postprocessing, and Chenhao Tan's Python solution.
"""

from arxivedits.detex.opendetex import detex_file as detex_file
from arxivedits.detex.pandoc import pandoc_file as pandoc_file
