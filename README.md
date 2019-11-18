# Cloning Chenhao Tan's "A Corpus of Sentence-level Revisions in Academic Writing"

This document outlines the steps I took to recreate Chenhao's dataset in [A Corpus of Sentence-level Revisions in Academic Writing](https://chenhaot.com/pubs/statement-strength.pdf).

1. Extract textual content from papers that have multiple versions of tex source files.
   1. Find all papers on Arxiv with multiple versions of tex source files (BeautifulSoup)
   2. Download and extract the files.
2. Macro align of paper sections
   1. In each version, find sections with the same section titles, and assume that they are the same section.
3. Micro align sentences.
   (https://stackoverflow.com/questions/49904659/finding-the-maximum-sum-of-values-in-a-2d-array-with-certain-restrictions)
   1. Extract sentences from a given section by taking any lines that do not begin with \{section} (or similar)
   2. Tokenize sentences with the Stanford tokenizer
   3. Create sentence pairs for each sentence in a section (N2 number of pairs, where N is the number of sentences in a section)
   4. Find the longest common subsequence for each sentence pair.
   5. Then use the above formula to calculate the similarity of two sentences. From Regina Barzilay, Noemie Elhadad, "Sentence Alignment for Monolingual Comparable Corpora", let ...
   6. Calculate s(i, j) for each sentence pair in the pool (still N2)
   7. Use a dynamic programming algorithm to find the optimal pairing of sentences

## 1. Extract textual content from papers that have multiple versions of tex source files.

### 1.1. Find all papers on Arxiv with multiple versions of tex source files (BeautifulSoup)

- Looked at https://github.com/Mahdisadjadi/arxivscraper, but it didn't let us select files by having more than one revision.
- https://arxiv.org/help/bulk_data
- https://arxiv.org/help/bulk_data_s3

#### Notes

- It looks like you can't ask for all papers with revisions. However, you can simply get all papers in a time date.
- The `arxivscraper` package uses an xml tree parser in Python. Is there a better xml tree parsers? (TODO)
- I think we'll need a database to see which papers we've looked up, as well as a place to store all of the raw text.
- We need to find every single paper on arxiv

From [arxiv](https://arxiv.org/help/arxiv_identifier):

Summary here

> In general, the form is `arXiv:YYMM.number{vV}`, where
>
> - `YY` is the two-digit year (07=2007 through 99=2099, and potentially up to 06=2106)
> - `MM` is the two-digit month number (01=Jan,...12=Dec)
> - number is a zero-padded sequence number of 4- or 5-digits. From `0704` through `1412` it is 4-digits, starting at `0001`. From `1501` on it is 5-digits, starting at `00001`. 5-digits permits up to 99999 submissions per month. We cannot currently anticipate more then 99999 submissions per month although extension to 6-digits would be possible.
> - `vV` is a literal `v` followed by a version number of 1 or more digits starting at `v1`.

**Can scrape Arxiv by iterating through arXiv:YYMM.number{vV} and looking for a v2 for every number. If there is no `v2` version, then don't download. If there is a v2, download v1, v1, and look for vN, where N starts at 3 and increases if vN exists.**

## Scaling

From [arxiv](https://arxiv.org/stats/monthly_submissions), there are (at the time of writing) 1,596,221 papers available. We will make at _a minimum_ ~1.6M requests because we might look for additional versions of some papers.

Rough calculations: we make 2M requests, we download (estimating based on "For instance, among the 70K papers submitted in 2011, almost 40% (27.7K) have multiple versions.") 40% of these requests, so 800K papers. One source file was 256KB (zipped), and the relevant text file was 37KB.

Based on these estimates, we will download 800K \* 256KB = 204,800,000KB = 204,800MB = **204GB**.

- TODO: revises these estimates as we begin downloading data.

# To Do

- might want to use https://docs.python.org/3.7/library/tempfile.html#module-tempfile
- could use https://code.google.com/archive/p/opendetex to scrape text from latex ->

```bash
brew install opendetex
python main.py | detex -r > parsed_test.txt # can pipe stuff straight into detex and then into a file
```

- Could use NLTK to parse the sentences. https://www.nltk.org/data.html

# Questions

- Research credit hours - CSE 4998H - Undergraduate Research in Computer Science and Engineering

## Development

```bash
find . -name '*.py' | entr pytest

pytest  --cov=arxivedits/
```

## Style Guide

- snake_case for functions
