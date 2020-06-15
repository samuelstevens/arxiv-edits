"""
Module to visualize a heatmap of similarities between two versions of a document.
"""
import os
import numpy as np
from enum import Enum
from typing import Callable, Optional, Any

from tqdm import tqdm

from arxivedits import data, diff, util, similarity
from arxivedits.alignment.align import (
    Alignment,
    easy_align,
    easy_align_outside_doc,
    process_easy_align,
)

ALIGN_MODE = Enum("ALIGN_MODE", ["ALL", "DIFF", "EASY", "GOLD"])
LABEL = Enum("LABEL", ["ALIGNED", "UNKNOWN", "BORING"])


def make_cell(value: float, tip: Optional[str] = "") -> str:
    """
    Makes a span.cell with a background color `color`.

    Parameters
    ----------

    value : str
        Similarity of the cell.
    tip : str, optional
        If included, it will be made visibile when the mouse hovers over the cell. Could be the sentence pair's ids, or their actual content, etc.
    """
    color = make_color_code(value)

    tip_str = f' tip="{tip}"' if tip else ""

    return f'<span class="cell"{tip_str} style="background-color: {color};"></span>'


def make_color_code(value: float) -> str:
    """
    For a similarity value, produces a color code. The following values are "special", in that they don't blend from black to red.

    -1 : BORING; all white (#ffffff)
    1 : MATCH; red (#ff0000)
    """
    if value == -1:
        color = "#ffffff"
    elif value == 1:
        color = "#ff0000"
    else:
        color = f"rgb({value * 255},0,0)"

    return color


def make_table(
    arxivid: str,
    v1: int,
    v2: int,
    mode: ALIGN_MODE,
    use_cache: bool = True,
    similarity_func: Optional[Callable[[str, str], float]] = None,
) -> np.ndarray:
    """
    Given a document pair and an ALIGN_MODE, calculates the approriate similarities. The matrix dimensions will always be len(v1) x len(v2) in size.

    Parameters
    ----------
    mode: ALIGN_MODE

    use_cache : bool, optional
        If false, will recalculate the table. Otherwise, it will use the locally written file with the table.
    similarity_func : Callable[[str, str], float], optional
        A function that takes two sentences and returns a similarity measure. If none is provided, then a diff-based algorithm will be used.
    """

    if not similarity_func:
        similarity_func = lambda x, y: similarity.get_similarity(x, y).diff_sim

    filename = os.path.join(
        data.ALIGNMENT_DIR, "similarity", f"{arxivid}-{v1}-{v2}-{mode}-table.npy",
    )

    if os.path.isfile(filename) and use_cache:
        return np.load(filename)

    print("Making table.")

    pgs1 = data.get_paragraphs(arxivid, v1)
    pgs2 = data.get_paragraphs(arxivid, v2)

    if isinstance(pgs1, Exception) or isinstance(pgs2, Exception):
        print("Failed to make table.")
        return

    lines1 = util.paragraphs_to_lines(pgs1)
    lines2 = util.paragraphs_to_lines(pgs2)

    BORING_VALUE = -1.0
    ALIGNED_VALUE = 1.0

    table = np.full((len(lines1), len(lines2)), BORING_VALUE, dtype=np.float_)

    if mode == ALIGN_MODE.ALL:
        for x, line1 in enumerate(lines1):
            for y, line2 in enumerate(lines2):
                table[x, y] = similarity_func(line1, line2)
    elif mode == ALIGN_MODE.DIFF:
        diff_alignment = Alignment(arxivid, v1, v2)
        for x, _id1 in enumerate(sorted(diff_alignment.alignments1.keys())):
            for y, _id2 in enumerate(sorted(diff_alignment.alignments2.keys())):
                if (
                    _id2 in diff_alignment.alignments1[_id1]
                    or _id1 in diff_alignment.alignments2[_id2]
                ):
                    table[x, y] = ALIGNED_VALUE
                    continue

                if diff_alignment.is_aligned(_id1) or diff_alignment.is_aligned(_id2):
                    table[x, y] = BORING_VALUE
                    continue

                table[x, y] = similarity_func(
                    diff_alignment.lookup[_id1], diff_alignment.lookup[_id2]
                )

    elif mode == ALIGN_MODE.EASY:
        diff_alignment = Alignment(arxivid, v1, v2)
        easy_alignments = easy_align(arxivid, v1, v2)
        process_easy_align(easy_alignments, diff_alignment)

        easy_alignments_outside = easy_align_outside_doc(easy_alignments)
        process_easy_align(easy_alignments_outside, diff_alignment)
        diff._hashable_line_diff.cache_clear()  # clear it after finishing a document

        for x, _id1 in enumerate(sorted(diff_alignment.alignments1.keys())):
            for y, _id2 in enumerate(sorted(diff_alignment.alignments2.keys())):
                if (
                    _id2 in diff_alignment.alignments1[_id1]
                    or _id1 in diff_alignment.alignments2[_id2]
                ):
                    table[x, y] = ALIGNED_VALUE
                    continue

                if diff_alignment.is_aligned(_id1) or diff_alignment.is_aligned(_id2):
                    table[x, y] = BORING_VALUE
                    continue

                table[x, y] = similarity_func(
                    diff_alignment.lookup[_id1], diff_alignment.lookup[_id2]
                )
    elif mode == ALIGN_MODE.GOLD:
        gold_alignment = Alignment.load(arxivid, v1, v2)
        for x, _id1 in enumerate(sorted(gold_alignment.alignments1.keys())):
            for y, _id2 in enumerate(sorted(gold_alignment.alignments2.keys())):
                if (
                    _id2 in gold_alignment.alignments1[_id1]
                    or _id1 in gold_alignment.alignments2[_id2]
                ):
                    table[x, y] = ALIGNED_VALUE
                    continue

                if gold_alignment.is_aligned(_id1) or gold_alignment.is_aligned(_id2):
                    table[x, y] = BORING_VALUE
                    continue

                table[x, y] = similarity_func(
                    gold_alignment.lookup[_id1], gold_alignment.lookup[_id2]
                )

    else:
        raise ValueError(f"Mode {mode} must be a valid ALIGN_MODE.")

    np.save(filename, table)

    return table


PREHTML = r"""<style>
  div {
    font-size: 0;
  }

  .cell {
    width: 5px;
    height: 5px;
    display: inline-block;
    margin: 0;
    position: relative;
  }
  
  .cell:hover {
      background-color: blue !important;
  }
  
  .cell[tip]:hover::after {
    content: attr(tip);
    position: absolute;
    left: 0;
    top: 24px;
    min-width: 100px;
    border: 1px #aaaaaa solid;
    border-radius: 10px;
    background-color: #ffffcc;
    padding: 12px;
    color: #000000;
    font-size: 14px;
    z-index: 1;
 }
</style>
<p><span style="color:red;">Red</span> means similar. White means identical. Black means not very similar</p>
<div>"""

POSTHTML = r"""</div>"""


def write_heatmap(
    arxivid: str, v1: int, v2: int, mode: ALIGN_MODE, filename: str = "", **kwargs: Any
) -> str:
    """
    Given a document pair and an ALIGN_MODE, creates a heatmap of similarities and writes it to an HTML file.

    Parameters
    ----------
    filename : str
        A different filename to use.
    **kwargs :
        keyword arguments to pass to make_table.
    """
    if not filename:
        filename = os.path.join(
            data.VISUAL_DIR, "heatmaps", f"{arxivid}-{v1}-{v2}-heatmap.html",
        )

    table = make_table(arxivid, v1, v2, mode, **kwargs)

    with open(filename, "w") as htmlfile:
        htmlfile.write(PREHTML)
        for x, row in enumerate(table):
            for y, value in enumerate(row):
                tip = f"v1:{x} v2:{y}" if value > 0 else None
                htmlfile.write(make_cell(value, tip=tip))
            htmlfile.write("<br/>")

        htmlfile.write(POSTHTML)

    return filename


def main() -> None:
    """
    Makes a heatmap for every annotated document.
    """
    for arxivid, v1, v2 in tqdm(data.ANNOTATED_IDS):
        write_heatmap(arxivid, v1, v2, ALIGN_MODE.DIFF)


if __name__ == "__main__":
    main()
