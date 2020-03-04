"""
Exports `pandoc_file()`, which uses `pandoc` and post processing (TODO) to extract text.
"""

import subprocess
import logging
from typing import Optional

from arxivedits.detex import latex


def pandoc_file(
    inputfile, outputfile, to="markdown", clean=True
) -> Optional[Exception]:
    with open(inputfile, "r") as file:
        content = file.read()

    if clean:
        content = latex.clean(content)

    try:
        result = subprocess.run(
            [
                "pandoc",
                "--from",
                "latex",
                "--to",
                to,
                "--standalone",
                "--atx-headers",
                "--output",
                outputfile,
            ],
            input=content,
            text=True,
            timeout=5,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        return Exception(f"Timed out on {inputfile}")
    else:
        if result and result.returncode != 0:
            logging.error(result.stderr)
            return Exception(f"Error with {inputfile}")
        return None
