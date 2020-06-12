import os, csv
import data, util
import alignment.util
import tqdm


def corpus_overview() -> None:

    with open(os.path.join(data.DATA_DIR, "sample-only-multiversion.csv")) as csvfile:
        reader = csv.reader(csvfile)
        sampled_ids = [(i, int(versioncount)) for i, versioncount in reader]

    total_pairs = 0
    idlist = []

    for arxivid, versioncount in sampled_ids:
        versionlist = list(range(1, versioncount + 1))

        idlist.extend([(arxivid, v) for v in versionlist])

        total_pairs += versioncount - 1

    print(len(idlist))

    idlist = [
        (arxivid, v)
        for arxivid, v in idlist
        if os.path.isfile(data.latex_path(arxivid, v))
    ]

    idset = set(idlist)

    total_tex = 0

    for arxivid, v in idlist:
        if (arxivid, v - 1) in idset:
            total_tex += 1
        elif v > 1:
            print(f"no pair for {arxivid}-{v}")

    total_sents = 0
    total_words = 0

    for arxivid, v in tqdm.tqdm(idset):
        pgs = data.get_paragraphs(arxivid, v)

        sents = util.flatten(pgs)

        sents = [s for s in sents if s]

        for sent in sents:
            words = util.sent_to_words(alignment.util.preprocess_single_sent(sent))
            total_words += len(words)

        total_sents += len(sents)

    print("Sample docs:", len(sampled_ids))
    print("Docs with source:", total_tex)
    print("Version pairs:", total_pairs)
    print("Total sents:", total_sents)
    print("Total words:", total_words)


if __name__ == "__main__":
    corpus_overview()
