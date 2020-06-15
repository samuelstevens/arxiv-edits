"""
Generates stats for arXiv as a data source.

* Might want to take a random sample of papers with 2+ versions, and a sample of all papers.
* From the random sample, write the arxiv ids to a text file
* From the text file, scrape all the papers + versions.
* From the text file and for all downloaded papers, measure the following statistics
    * total # of papers
    * total #, % of papers with 2+ versions
    * total # of revision pairs: (1, 2), (2, 3), etc
    * % of sentences with embedded LaTeX
    * % of sentences deleted
    * % of sentences modified (>= 4 in distance)
    * % of sentences with typos (< 4 in distance)
"""
import os
import csv
from typing import List, Tuple


from arxivedits import data, source


MULTIPLE_VERSIONS = True
SENTENCELENGTH = 20


def get_random_sample(
    samplesize: int = 1000, multipleversions: bool = MULTIPLE_VERSIONS
) -> List[Tuple[str, int]]:
    """
    Gets a new random sample unless one exists.
    """

    extension = "-only-multiversion" if multipleversions else "-all"

    samplefilepath = os.path.join(data.DATA_DIR, f"sample{extension}.csv")

    if os.path.isfile(samplefilepath):
        with open(samplefilepath, "r") as csvfile:
            reader = csv.reader(csvfile)
            ids = [(arxivid, int(versioncount)) for arxivid, versioncount in reader]
        return ids

    con = data.connection()

    if multipleversions:
        query = "SELECT * FROM papers WHERE version_count > 1 ORDER BY RANDOM() LIMIT ?"
    else:
        query = "SELECT * FROM papers ORDER BY RANDOM() LIMIT ?"

    sample = con.execute(query, (samplesize,)).fetchall()

    with open(samplefilepath, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(sample)

    return [(arxivid, versioncount) for arxivid, versioncount in sample]


def main() -> None:
    """
    Takes a random sample and writes them to a text file. Then calculates stats.
    """

    sample = get_random_sample(multipleversions=True)

    # takes a smaller sample
    sample = sample[:200]

    print(f"{len(sample)} ids in sample.")

    downloadcount = len(sample)

    for arxivid, versioncount in sample:
        if source.is_downloaded(arxivid, versioncount):
            downloadcount -= 1

    print(
        f"{downloadcount} to download. Estimated {downloadcount * 2 * 30 / 60 / 60:.1f} hours ({downloadcount * 2 * 30 / 60 :.0f} minutes)."
    )

    for arxivid, versioncount in sample:
        source.download_source_files(arxivid, versioncount)

    # source.extract_all()
    # tex.main()
    # sections.main()
    # tokenizer.main()


if __name__ == "__main__":
    main()
