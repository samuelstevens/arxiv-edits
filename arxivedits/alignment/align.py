"""
Alignment class and helper routines
"""

import os
import csv
import pickle
import logging

from typing import Dict, List, Tuple, Set, Optional, Any, cast


from arxivedits import data, util, diff
from arxivedits.alignment.sentence import SentenceID
from arxivedits.alignment.structures import SentenceStruct, DiffStruct, STATUS
from arxivedits.alignment.util import (
    similar,
    is_paragraph_solved,
    is_sentence_solved,
)


def to_diff_with_ids(
    line_diff: diff.LineDiff, arxivid: str, version1: int, version2: int
) -> List[Tuple[int, str, List[SentenceID]]]:
    """
    Converts a basic diff to a diff with the corresponding SentenceIDs
    """
    paragraph_index_1 = 0
    sentence_index_1 = 0

    paragraph_index_2 = 0
    sentence_index_2 = 0

    diff_with_ids = []

    sentence_ids: List[SentenceID]

    for code, sent in line_diff:
        if code == -1:
            sentence_ids = [
                SentenceID(arxivid, version1, paragraph_index_1, sentence_index_1),
            ]

        elif code == 1:
            sentence_ids = [
                SentenceID(arxivid, version2, paragraph_index_2, sentence_index_2),
            ]
        elif code == 0:
            sentence_ids = [
                SentenceID(arxivid, version1, paragraph_index_1, sentence_index_1),
                SentenceID(arxivid, version2, paragraph_index_2, sentence_index_2),
            ]
        else:
            raise ValueError(f"code {code} must be -1, 0 or 1.")

        diff_with_ids.append((code, sent, sentence_ids))

        if code in [-1, 0]:  # old version
            sentence_index_1 += 1

        if code in [0, 1]:  # new version
            sentence_index_2 += 1

        if sent == "":
            if code in [-1, 0]:  # old version
                paragraph_index_1 += 1
                sentence_index_1 = 0

            if code in [0, 1]:  # addition
                paragraph_index_2 += 1
                sentence_index_2 = 0

    return diff_with_ids


def identical_align(
    arxivid: str, version1: int, version2: int
) -> Tuple[
    Dict[SentenceID, Set[SentenceID]],
    Dict[SentenceID, Set[SentenceID]],
    Dict[SentenceID, str],
]:
    """
    Uses a simple diff algorithm to find all identical sentences for an Alignment class. Returns dictionaries for the alignments and the lookup from SentenceID to sentence string.
    """
    assert (
        version1 < version2
    ), f"version 1 {version1} must be smaller than version 2 {version2}!"
    assert os.path.isfile(
        data.sentence_path(arxivid, version1)
    ), f"{arxivid}-{version1} must have a sentences.txt!"
    assert os.path.isfile(
        data.sentence_path(arxivid, version2)
    ), f"{arxivid}-{version2} must have a sentences.txt!"

    align1: Dict[SentenceID, Set[SentenceID]] = {}
    align2: Dict[SentenceID, Set[SentenceID]] = {}

    doc1 = data.get_paragraphs(arxivid, version1)
    doc2 = data.get_paragraphs(arxivid, version2)

    if isinstance(doc1, Exception):
        raise doc1

    if isinstance(doc2, Exception):
        raise doc2

    lines1 = util.paragraphs_to_lines(doc1)
    lines2 = util.paragraphs_to_lines(doc2)

    line_diff = diff.line_diff(lines1, lines2)

    line_diff_with_ids = to_diff_with_ids(line_diff, arxivid, version1, version2)

    lookup: Dict[SentenceID, str] = {}

    for code, sent, ids in line_diff_with_ids:
        if code == 0:
            assert len(ids) == 2
            id1, id2 = ids

            lookup[id1] = sent
            lookup[id2] = sent

            align1[id1] = set([id2])
            align2[id2] = set([id1])

        elif code == -1:
            id1 = ids[0]

            lookup[id1] = sent
            align1[id1] = set()

        elif code == 1:
            id2 = ids[0]

            lookup[id2] = sent
            align2[id2] = set()

        else:
            raise ValueError(f"code {code} must be one of -1, 0, 1")

    return align1, align2, lookup


# Easy alignment of one document
def easy_align(
    arxivid: str, version1: int, version2: int
) -> List[List[SentenceStruct]]:
    """
    Uses a simple threshold to align sentences within the same paragraph (counted using line breaks).
    """
    assert (
        version1 < version2
    ), f"version 1 {version1} must be smaller than version 2 {version2}!"
    assert os.path.isfile(
        data.sentence_path(arxivid, version1)
    ), f"{arxivid}-{version1} must have a sentences.txt!"
    assert os.path.isfile(
        data.sentence_path(arxivid, version2)
    ), f"{arxivid}-{version2} must have a sentences.txt!"

    doc1 = data.get_paragraphs(arxivid, version1)
    doc2 = data.get_paragraphs(arxivid, version2)

    if isinstance(doc1, Exception):
        raise doc1

    if isinstance(doc2, Exception):
        raise doc2

    lines1 = util.paragraphs_to_lines(doc1)
    lines2 = util.paragraphs_to_lines(doc2)

    line_diff = diff.line_diff(lines1, lines2)

    line_diff_with_ids = to_diff_with_ids(line_diff, arxivid, version1, version2)

    idx_and_content_grouped_by_paragraph = []
    current_paragraph = []
    aligned_paragraphs = []

    for i, (code, sent_str, identifiers) in enumerate(line_diff_with_ids):
        current_paragraph.append((i, (code, sent_str, identifiers)))

        if sent_str == "" and code in [0, -1]:
            idx_and_content_grouped_by_paragraph.append(current_paragraph)
            current_paragraph = []

    if current_paragraph:
        idx_and_content_grouped_by_paragraph.append(current_paragraph)

    for original_pg in idx_and_content_grouped_by_paragraph:
        pg = [
            SentenceStruct(
                index=global_idx,
                identifiers=identifiers,
                diff=DiffStruct(code, sent),
                status=STATUS.UNKNOWN,
                aligned=set(),
            )
            for sent_idx, (global_idx, (code, sent, identifiers)) in enumerate(
                original_pg
            )
        ]
        for sent in pg:
            if sent.diff.code == 0:
                sent.status = STATUS.SOLVED
                sent.aligned.add(sent.index)

        removed_sent_indices = [
            i for i, sentence in enumerate(pg) if sentence.diff.code == -1
        ]
        added_sent_indices = [
            i for i, sentence in enumerate(pg) if sentence.diff.code == 1
        ]

        for removed_sent_idx in removed_sent_indices:
            if diff.is_title_or_newline(pg[removed_sent_idx].diff.sentence):
                pg[removed_sent_idx].status = STATUS.BORING  # changed from Chao's code
                continue

            if not diff.sent_filter(pg[removed_sent_idx].diff.sentence):
                pg[removed_sent_idx].status = STATUS.BORING
                continue

            for added_sent_idx in added_sent_indices:

                if diff.is_title_or_newline(pg[added_sent_idx].diff.sentence):
                    pg[
                        added_sent_idx
                    ].status = STATUS.BORING  # changed from Chao's code
                    continue

                if not diff.sent_filter(pg[added_sent_idx].diff.sentence):
                    pg[added_sent_idx].status = STATUS.BORING
                    continue

                the_sent_got_removed = pg[removed_sent_idx].diff.sentence
                the_sent_got_added = pg[added_sent_idx].diff.sentence

                if similar(the_sent_got_removed, the_sent_got_added):
                    pg[removed_sent_idx].status = STATUS.SOLVED
                    pg[removed_sent_idx].aligned.add(pg[added_sent_idx].index)

                    pg[added_sent_idx].status = STATUS.USED
                    pg[added_sent_idx].aligned.add(pg[removed_sent_idx].index)

        aligned_paragraphs.append(pg)

    return aligned_paragraphs


def easy_align_outside_doc(
    partially_aligned_paragraphs: List[List[SentenceStruct]],
) -> List[List[SentenceStruct]]:
    """
    TODO: consider refactoring. Right now, a lot of code is shared between the easy_align functions.
    """

    unsolved_paragraphs = [
        pg for pg in partially_aligned_paragraphs if not is_paragraph_solved(pg)
    ]

    removed_sentences = []
    added_sentences = []

    for pg in unsolved_paragraphs:
        for sentence in pg:
            if (
                not is_sentence_solved(sentence)
                and sentence.diff.code == -1
                and diff.sent_filter(sentence.diff.sentence)
            ):
                removed_sentences.append(sentence)

    for pg in partially_aligned_paragraphs:
        for sentence in pg:
            if (
                not is_sentence_solved(sentence)
                and sentence.diff.code == 1
                and diff.sent_filter(sentence.diff.sentence)
            ):
                added_sentences.append(sentence)

    aligned_sentences: List[SentenceStruct] = []

    for removed_sentence in removed_sentences:
        if diff.is_title_or_newline(removed_sentence.diff.sentence):
            continue

        if not diff.sent_filter(removed_sentence.diff.sentence):
            continue

        for added_sentence in added_sentences:
            if diff.is_title_or_newline(added_sentence.diff.sentence):
                continue

            if not diff.sent_filter(added_sentence.diff.sentence):
                continue

            the_sent_got_removed = removed_sentence.diff.sentence
            the_sent_got_added = added_sentence.diff.sentence

            if similar(the_sent_got_removed, the_sent_got_added):
                removed_sentence.status = STATUS.SOLVED
                removed_sentence.aligned.add(added_sentence.index)
                aligned_sentences.append(removed_sentence)

                added_sentence.status = STATUS.USED
                added_sentence.aligned.add(removed_sentence.index)
                aligned_sentences.append(added_sentence)

    return [aligned_sentences]


def parse_csv_row(row: List[str]) -> Tuple[SentenceID, str, SentenceID, str, int]:
    """
    Parses CSV rows in format `pair_ID|pair_UID|sent_0_idx|sent_0|sent_1_idx|sent_1|aligning_method` and returns the SentenceIDs and sentences
    """
    (
        _,
        _,
        new_from_sent_id_str,
        sent1,
        new_to_sent_id_str,
        sent2,
        alignment_method_str,
    ) = row

    alignment_method = int(alignment_method_str)
    new_from_sent_id = SentenceID.parse(new_from_sent_id_str)
    new_to_sent_id = SentenceID.parse(new_to_sent_id_str)

    return new_from_sent_id, sent1, new_to_sent_id, sent2, alignment_method


def process_easy_align(
    easy_alignments: List[List[SentenceStruct]], alignment: "Alignment"
) -> None:
    """
    Updates an alignment with the easy alignments.
    """
    lookup: Dict[int, SentenceStruct] = {}

    for pg in easy_alignments:
        for sentence in pg:
            lookup[sentence.index] = sentence

    for pg in easy_alignments:
        for sentence in pg:
            if sentence.diff.code == 0:
                continue  # already in alignment

            if sentence.diff.code == 1:
                # since we are only looking for sentences that are aligned, we can only look at deletions that are also aligned.
                continue

            if sentence.status in [STATUS.UNKNOWN, STATUS.BORING]:
                continue  # don't know what it's aligned to or we don't care

            assert sentence.diff.code == -1  # always an deleted sentence now
            assert sentence.status in [
                STATUS.SOLVED,
                STATUS.USED,
            ]  # always a possibly aligned sentence
            assert len(sentence.aligned) > 0, str(
                sentence
            )  # always at least one alignment

            assert len(sentence.identifiers) == 1, str(
                sentence
            )  # since deleted, only one identifier
            identifier = sentence.identifiers[0]

            assert identifier in alignment.alignments1, str(sentence)

            aligned_ids = [
                sentence_id
                for index in lookup[sentence.index].aligned
                for sentence_id in lookup[index].identifiers
            ]

            for sentence_id in aligned_ids:
                alignment.alignments1[identifier].add(sentence_id)
                alignment.alignments2[sentence_id].add(identifier)


class Alignment:
    """
    Represents an alignment between two versions of a document, using SentenceID to keep track of sentences.
    """

    def __init__(self, arxivid: str, version1: int, version2: int):
        assert (
            version1 < version2
        ), f"version 1 {version1} must be smaller than version 2 {version2}!"
        assert os.path.isfile(
            data.sentence_path(arxivid, version1)
        ), f"{arxivid}-{version1} must have a sentences.txt!"
        assert os.path.isfile(
            data.sentence_path(arxivid, version2)
        ), f"{arxivid}-{version2} must have a sentences.txt!"

        self.arxivid = arxivid
        self.version1 = version1
        self.version2 = version2

        align1, align2, lookup = identical_align(arxivid, version1, version2)

        self.alignments1: Dict[SentenceID, Set[SentenceID]] = align1
        self.alignments2: Dict[SentenceID, Set[SentenceID]] = align2
        self.lookup: Dict[SentenceID, str] = lookup

        self.new_to_old_lookup: Dict[SentenceID, SentenceID] = {}

        self.write_unaligned_csv()  # populates self.new_to_old_lookup
        self.save()

    def is_aligned(self, sentence_id: SentenceID) -> bool:
        """
        Checks whether a sentence has been aligned.
        """
        if sentence_id.arxivid != self.arxivid:
            return False

        if sentence_id.version == self.version1:
            return bool(self.alignments1[sentence_id])
        elif sentence_id.version == self.version2:
            return bool(self.alignments2[sentence_id])
        else:
            raise ValueError(
                f"{sentence_id} is not version {self.version1} or {self.version2}"
            )

    def get_unaligned(self) -> List[SentenceID]:
        """
        Returns a list of all the unaligned sentence ids, both from the first and second versions.
        """
        unaligned = [
            _id
            for _id in self.lookup
            if not self.is_aligned(_id) and not diff.is_boring(self.lookup[_id])
        ]

        return unaligned

    def __str__(self) -> str:
        return f"<Alignment of {self.arxivid}-v{self.version1}-v{self.version2}>"

    def __repr__(self) -> str:
        return self.__str__()

    def save(self) -> None:
        """
        Saves self as a .pckl file in the appropriate folder. Creates a filename based on arxivid, version1 and version2.
        """

        filepath = data.alignment_model_path(
            self.arxivid, self.version1, self.version2, len(self.get_unaligned())
        )

        if os.path.isfile(filepath):  # file already exists.
            with open(filepath, "rb") as loadfile:
                other_alignment: Alignment = cast("Alignment", pickle.load(loadfile))

            if len(other_alignment.get_unaligned()) < len(self.get_unaligned()):
                logging.warning(
                    "Existing .pckl file for %s has fewer (%d < %d) unaligned sentences. Not overwriting.",
                    str(other_alignment),
                    len(other_alignment.get_unaligned()),
                    len(self.get_unaligned()),
                )
                return

        with open(filepath, "wb") as savefile:
            pickle.dump(self, savefile, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(
        arxivid: str,
        version1: int,
        version2: int,
        unaligned_sentences: Optional[int] = None,
    ) -> "Alignment":
        """
        Loads a .pckl file from the appropriate folder and returns the Alignment instance.
        """

        if not unaligned_sentences:
            unaligned_sentences = 0
            possible_path = data.alignment_model_path(
                arxivid, version1, version2, unaligned_sentences
            )
            while not os.path.isfile(possible_path) and unaligned_sentences < 1000:
                unaligned_sentences += 1
                possible_path = data.alignment_model_path(
                    arxivid, version1, version2, unaligned_sentences
                )

            if unaligned_sentences == 1000:
                raise ValueError(
                    f"Could not find file at {possible_path} with any number of unaligned sentences"
                )

        filepath = data.alignment_model_path(
            arxivid, version1, version2, unaligned_sentences
        )

        with open(filepath, "rb") as loadfile:
            return cast("Alignment", pickle.load(loadfile))

    @staticmethod
    def load_csv(arxivid: str, version1: int, version2: int) -> "Alignment":
        """
        Loads the .csv file for an entire alignment from the appropriate folder and returns the Alignment instance.
        """

        filepath = data.alignment_csv_path(arxivid, version1, version2)

        alignment = Alignment(arxivid, version1, version2)

        with open(filepath, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter="|", quoting=csv.QUOTE_MINIMAL)

            next(reader)  # get past initial header row

            for row in reader:
                (
                    from_sent_id,
                    sent1,
                    to_sent_id,
                    sent2,
                    alignment_method,
                ) = parse_csv_row(row)

                if from_sent_id in alignment.lookup:
                    assert alignment.lookup[from_sent_id] == sent1
                else:
                    alignment.lookup[from_sent_id] = sent1

                if to_sent_id in alignment.lookup:
                    assert alignment.lookup[to_sent_id] == sent2
                else:
                    alignment.lookup[to_sent_id] = sent2

                if alignment_method == 3:
                    continue  # not aligned

                elif alignment_method == 2:
                    continue  # partial alignment; TODO

                elif alignment_method == 1:
                    # fully aligned
                    alignment.alignments1[from_sent_id].add(to_sent_id)
                    alignment.alignments2[to_sent_id].add(from_sent_id)

                else:
                    raise ValueError(
                        f"alignment method '{alignment_method}' must be one of: 1, 2, 3"
                    )

        return alignment

    def write_csv(self, group: str = "") -> None:
        """
        Writes itself as a .csv file for later user.

        Format:
        pair_ID|pair_UID|sent_0_idx|sent_0|sent_1_idx|sent_1|aligning_method
        """
        if group == "machine":
            filepath = data.machine_csv_path(self.arxivid, self.version1, self.version2)
        else:
            filepath = data.alignment_csv_path(
                self.arxivid, self.version1, self.version2
            )

        with open(filepath, "w") as csvfile:
            writer = csv.writer(csvfile, delimiter="|", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "pair_ID",
                    "pair_UID",
                    "sent_0_idx",
                    "sent_0",
                    "sent_1_idx",
                    "sent_1",
                    "aligning_method",
                ]
            )

            for from_sent_id in self.alignments1:
                for to_sent_id in self.alignments2:
                    aligned = 1 if to_sent_id in self.alignments1[from_sent_id] else 3

                    version1_id = f"{from_sent_id.version}-{from_sent_id.paragraph_index}-{from_sent_id.sentence_index}"
                    version2_id = f"{to_sent_id.version}-{to_sent_id.paragraph_index}-{to_sent_id.sentence_index}"

                    pair_id = f"ID-{self.arxivid}-{version1_id}-{version2_id}"
                    row = [
                        pair_id,
                        "UID",
                        str(from_sent_id),
                        self.lookup[from_sent_id],
                        str(to_sent_id),
                        self.lookup[to_sent_id],
                        aligned,
                    ]

                    writer.writerow(row)

    def write_unaligned_csv(self) -> None:
        """
        Writes all the unaligned sentence to a .csv for the HTML viewer/annotater tool to open. This creates the internal new_to_old lookup dictionary
        """
        filepath = data.alignment_annotation_path(
            self.arxivid, self.version1, self.version2, len(self.get_unaligned())
        )

        if os.path.isfile(filepath):
            return

        unaligned = sorted(self.get_unaligned())

        version1 = []
        version2 = []

        paragraph_count = -1
        prev_pg = -1

        sentence_count = 0
        i = 0

        while i < len(unaligned):
            if (
                unaligned[i].paragraph_index != prev_pg
            ):  # if we switch paragraph, reset sentence count
                prev_pg = unaligned[i].paragraph_index
                paragraph_count += 1
                sentence_count = 0

            if (
                i > 0 and unaligned[i].version != unaligned[i - 1].version
            ):  # if we switch version, reset all counts
                prev_pg = -1
                paragraph_count = 0
                sentence_count = 0

            new_id = SentenceID(
                self.arxivid, unaligned[i].version, paragraph_count, sentence_count
            )
            self.new_to_old_lookup[new_id] = unaligned[i]

            if new_id.version == self.version1:
                version1.append(new_id)
            elif new_id.version == self.version2:
                version2.append(new_id)
            else:
                raise ValueError(
                    f"{new_id} is not version {self.version1} or {self.version2}"
                )

            sentence_count += 1
            i += 1

        with open(filepath, "w") as csvfile:
            writer = csv.writer(csvfile, delimiter="|", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "pair_ID",
                    "pair_UID",
                    "sent_0_idx",
                    "sent_0",
                    "sent_1_idx",
                    "sent_1",
                    "aligning_method",
                ]
            )

            for new_from_sent_id in version1:
                for new_to_sent_id in version2:
                    aligned = 3  # never aligned

                    version1_id = f"{new_from_sent_id.version}-{new_from_sent_id.paragraph_index}-{new_from_sent_id.sentence_index}"
                    version2_id = f"{new_to_sent_id.version}-{new_to_sent_id.paragraph_index}-{new_to_sent_id.sentence_index}"

                    pair_id = f"ID-{self.arxivid}-{version1_id}-{version2_id}"
                    row = [
                        pair_id,
                        "UID",
                        str(new_from_sent_id),
                        self.lookup[self.new_to_old_lookup[new_from_sent_id]],
                        str(new_to_sent_id),
                        self.lookup[self.new_to_old_lookup[new_to_sent_id]],
                        aligned,
                    ]

                    writer.writerow(row)

        self.save()

    def read_unaligned_csv(self) -> None:
        """
        Reads a csv file that has the now manually aligned sentences and adds the alignments to itself.
        """

        filepath = data.alignment_finished_path(
            self.arxivid, self.version1, self.version2, len(self.get_unaligned())
        )

        if not os.path.isfile(filepath):
            logging.warning(
                "Couldn't find a finished annotation file for %s", str(self)
            )
            return

        with open(filepath, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter="|", quoting=csv.QUOTE_MINIMAL)

            next(reader)  # get past initial header row

            for row in reader:
                (
                    new_from_sent_id,
                    _,
                    new_to_sent_id,
                    _,
                    alignment_method,
                ) = parse_csv_row(row)

                if alignment_method == 3:
                    continue  # not aligned

                elif alignment_method == 2:
                    continue  # partial alignment; TODO

                elif alignment_method == 1:
                    # fully aligned
                    if new_from_sent_id not in self.new_to_old_lookup:
                        print(new_from_sent_id)
                        print(sorted(self.new_to_old_lookup.items()))
                        raise ValueError(
                            "new_from_sent_id not in self.new_to_old_lookup"
                        )
                    real_from_sent_id = self.new_to_old_lookup[new_from_sent_id]
                    real_to_sent_id = self.new_to_old_lookup[new_to_sent_id]

                    if (
                        real_from_sent_id not in self.lookup
                        or real_from_sent_id not in self.alignments1
                    ):
                        raise ValueError(f"{real_from_sent_id} not in this alignment.")

                    if (
                        real_to_sent_id not in self.lookup
                        or real_to_sent_id not in self.alignments2
                    ):
                        raise ValueError(f"{real_to_sent_id} not in this alignment.")

                    self.alignments1[real_from_sent_id].add(real_to_sent_id)
                    self.alignments2[real_to_sent_id].add(real_from_sent_id)
                else:
                    raise ValueError(
                        f"alignment method '{alignment_method}' must be one of: 1, 2, 3"
                    )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Alignment):
            return False

        return (
            self.alignments1 == other.alignments1
            and self.alignments2 == other.alignments2
            and self.lookup == other.lookup
            and self.get_unaligned() == other.get_unaligned()
        )
