from typing import Any


class SentenceID:
    """
    An id for any given sentence in a document. The sentences are 0-indexed from the start of their paragraph.
    """

    def __init__(
        self, arxivid: str, version: int, paragraph_index: int, sentence_index: int
    ):
        """
        sentence_index is index within a paragraph (0-indexed)
        """
        self.arxivid = arxivid
        self.version = version
        self.paragraph_index = paragraph_index
        self.sentence_index = sentence_index

    def __str__(self) -> str:
        return f"{self.arxivid}-v{self.version}-{self.paragraph_index}-{self.sentence_index}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SentenceID):
            return (
                self.arxivid == other.arxivid
                and self.version == other.version
                and self.paragraph_index == other.paragraph_index
                and self.sentence_index == other.sentence_index
            )
        return False

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(
            (self.arxivid, self.version, self.paragraph_index, self.sentence_index)
        )

    def __lt__(self, other: Any) -> bool:
        if self.version < other.version:
            return True
        elif self.version > other.version:
            return False

        if self.paragraph_index < other.paragraph_index:
            return True
        elif self.paragraph_index > other.paragraph_index:
            return False

        if self.sentence_index < other.sentence_index:
            return True
        elif self.sentence_index > other.sentence_index:
            return False

        return False  # equal

    @staticmethod
    def parse(stringified: str) -> "SentenceID":
        """
        parses 1701.01370-v1-0-0, and cond-math-v1-0-0, etc
        """

        *arxividlist, version_str, pg_idx_str, sent_idx_str = stringified.split("-")

        arxivid = "-".join(arxividlist)

        version = int(version_str[1:])  # remove the v

        pg_idx = int(pg_idx_str)

        sent_idx = int(sent_idx_str)

        return SentenceID(arxivid, version, pg_idx, sent_idx)


def main() -> None:
    print(SentenceID.parse("cond-math-v1-0-0"))


if __name__ == "__main__":
    main()
