import os

from typing import List, Set

from arxivedits.structures import T
from arxivedits import data
from arxivedits.alignment.align import Alignment
from arxivedits.alignment.sentence import SentenceID
from arxivedits.chunks.data import group_asserts


PRE_HTML = r"""<style>
  div {
    font-size: 0;
  }

  .cell {
    width: 10px;
    height: 40px;
    display: inline-block;
    margin: 0;
    position: relative;
  }

  .hover:hover {
    background-color: orange !important;
  }
  
  .cell[data-sent]:hover::after {
    content: attr(data-sent);
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
<p>Legend</p>
<p><span style="background-color: green; color: white;">Green</span>: True positive; predicted as part of a chunk and was actually part of a chunk.</p>
<p><span style="background-color: #99aedd; color: white;">Faded blue</span>: "Weak" false positive; predicted as part of a chunk, was <em>not</em> actually part of a chunk, but wasn't aligned anyways.</p>
<p><span style="background-color: yellow; color: black;">Yellow</span>: False negative; not predicted as part of a chunk, <em>was</em> actually part of a chunk.</p>
<p><span style="background-color: blue; color: white;">Blue</span>: False positive; predicted as part of a chunk, was <em>not</em> actually part of a chunk, <em>and</em> <strong>was an aligned sentence</strong>.</p>
<p><span style="background-color: #dddddd; color: black;">Gray</span>: True negative; wasn't predicted as part of a chunk, was not actually part of a chunk.</p>
<div>"""

POST_HTML = r"""</div>"""


def visualize_predictions(
    doc: List[SentenceID],
    predictions: Set[T],
    target: Set[T],
    alignment: Alignment,
    group: str,
) -> str:
    group_asserts(group)

    colors = []

    unaligned_sents_not_in_block = set(alignment.get_unaligned()) - target

    BLUE = predictions - unaligned_sents_not_in_block - target
    GREEN = predictions & target
    YELLOW = target - predictions
    FADED_BLUE = unaligned_sents_not_in_block & predictions

    assert predictions == BLUE | FADED_BLUE | GREEN
    assert target == GREEN | YELLOW

    #     for _id in sorted(BLUE):
    #         if _id.version == alignment.version1:
    #             for matched_id in alignment.alignments1[_id]:
    #                 print(alignment.lookup[_id])
    #                 print(alignment.lookup[matched_id])
    #                 print(arxivedits.similarity.get_similarity(alignment.lookup[_id], alignment.lookup[matched_id]))
    #             print()
    #         elif _id.version == alignment.version2:
    #             for matched_id in alignment.alignments2[_id]:
    #                 print(alignment.lookup[_id])
    #                 print(alignment.lookup[matched_id])
    #                 print(arxivedits.similarity.get_similarity(alignment.lookup[_id], alignment.lookup[matched_id]))
    #             print()

    for e in doc:
        count = 0
        if e in GREEN:
            color = "green"
            count += 1
        if e in BLUE:
            color = "blue"
            count += 1
        if e in YELLOW:
            color = "yellow"
            count += 1
        if e in FADED_BLUE:
            color = "#99aedd"
            count += 1
        if count == 0:
            color = "#dddddd"
            count += 1

        assert count == 1, f"{e}, {count}, {color}"

        colors.append(color)

    filename = os.path.join(
        data.VISUAL_DIR,
        "predictions",
        f"{alignment.arxivid}-{alignment.version1}-{alignment.version2}-{group}.html",
    )

    with open(filename, "w") as file:
        file.write(PRE_HTML)
        for color, _id in zip(colors, doc):
            file.write(
                f"""<span class="cell hover" data-sent="{alignment.lookup[_id]}" style="background-color: {color};"></span>\n"""
            )
        file.write(POST_HTML)

    return filename
