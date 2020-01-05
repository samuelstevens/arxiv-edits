# Arxiv Edits

## Introduction

arXiv can be used as a source of documents with revisions aimed at improving accuracy and clarity. At the time of writing, arXiv hosted 1,635,488 different papers, with 611,524 having two or more versions. Some papers have more than two versions. A more useful number is *version pairs*, of which there are 899,431. 

However, not all papers release their LaTeX source documents, or some documents are not valid LaTeX. From a sample of 50 random papers with two or more revisions, on average, 236 sentences were extracted per document, and 170 were extracted with no inline math. These numbers are lowered for several reasons:
1. Not all documents provide LaTeX source. PDFs were not parsed.
2. Not all LaTeX source documents were able to be "detexed". This is described in additional detail in [Approach](##Approach).

## Related Work and Background

arXiv has been used as source of edit data previously in order to measure statement strength ([@tan+lee:14]). Other openly available data with revisions include Wikipedia, which has been explored as a source of split and rephrasing data ([@split:emnlp18]) and for modeling discourse ([@pavlick:emnlp18]). 

## Approach

Because LaTeX source documents contain symbols and commands not normally used in the English language (\section, \begin{}, etc.), we extract the raw text before beginning sentence alignments. 

Open source tools include [OpenDetex](https://github.com/pkubowicz/opendetex) and [Pandoc](https://pandoc.org/). OpenDetex removes all inline math and replaces it with "noun" and "verb" in order to preserve grammar. Pandoc leaves inline math as is. Pandoc was chosen because it preserves more text, leading to greater flexibility later (inline math could later be replaced with custom tags such as [EQN] or [MATH]) for the sentence alignment algorithm. An improved "de-tex" algorithm would lead to a higher number of aligned sentences, or a higher quality of alignment. 

Because LaTeX source documents are typically organized into sections, macro alignment was performed by matching sections to each other using Levenshtein distance between section titles. 

Once text was extracted and sections aligned, Stanford's CoreNLP tokenizer was used to tokenize sentences. Because the tokenizer is designed to work with English sentences, LaTeX syntax caused problems. A list of common suffixes in incorrectly split sentences (Fig., Ref., Sec., etc.) was used to rejoin sentences if necessary. 

Multiple aligning algorithms were evaluated for the best alignment: MASSAlign [@paetzold-etal-2017-massalign], a weighted longest common subsequence (described by [@tan+lee:14] and inspired by [@barzilay+elhadad:03]), and a Neural CRF aligner [@jiang:20] (TODO).

## Evaluation

To produce the highest quality aligned dataset, each alignment algorithm was tested on a dataset of 352 manually aligned sentences from arXiv papers.

### Results

Results for the alignment algorithms MASSAlign and weighted LCS can be seen below.

#### MASSAlign
```
Precision: 0.84
Recall:    0.94
F1:        0.89
```

#### Weighted LCS
```
Precision: 0.70
Recall:    0.97
F1:        0.81
```

## Analysis

In some instances, the meaning of the sentence is changed deliberately: 

```
v1: We use all frames from one repetition of each action for training, and every 64$^{th}$ frame from all repetitions at test.

v2: We use all frames from one of the two instances of each action for training, and every 64$^{th}$ frame from all instances for testing.
```
Should these sentences be aligned? This is not an edit that further clarifies the meaning of the sentence; the research group could have changed their methodology between version 1 and 2 of the paper.

## Further Work

MASSAlign includes a section (paragraph) alignment algorithm that might be more effective than matching section titles via Levenshtein edit distance.

In addition, the algorithms should be tested on more than 352 sentences. In addition to manually aligning additional sentences, using other datasets that are revision-focused such as [@tan+lee:14], [@split:emnlp18] or [@pavlick:emnlp18] to evaluate the alignment algorithms would be useful. 

Further, the precision, recall, and F1 scores are all inflated due to the higher number of identical sentences. In order to accurately report the success of these algorithms, identical sentences between version n and version n+1 should be removed before the remaining sentences are aligned. 