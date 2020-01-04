# Arxiv Edits

## Introduction

arXiv can be used as a source of documents with revisions aimed at improving accuracy and clarity. At the time of writing, arXiv hosted 1,635,488 different papers, with 611,524 having two or more versions. Some papers have more than two versions. A more useful number is *version pairs*, of which there are 899,431. 

However, not all papers release their LaTeX source documents, or some documents are not valid LaTeX. From a sample of 50 random documents with two or more revisions, on average, 771 sentences were extracted per document, and 271 were extracted with no inline math. 

## Related Work and Background

arXiv has been used as source of edit data previously in order to measure statement strength ([@tan+lee:14]). Other openly available data with revisions include Wikipedia, which has been explored as a source of split and rephrasing data ([@split:emnlp18]). 

## Approach

Because LaTeX source documents contain symbols and commands not normally used in the English language (\section, \begin{}, etc.), we extract the raw text before beginning sentnce alignments. 

Open source tools include [OpenDetex](https://github.com/pkubowicz/opendetex) and [Pandoc](https://pandoc.org/). OpenDetex removes all inline math and replaces it with "noun" and "verb" in order to preserve grammar. Pandoc leaves inline math as is. Pandoc was chosen because it preserves more text, leading to greater flexibility later (inline math could later be replaced with custom tags such as [EQN] or [MATH]) for the sentence alignment algorithm. An improved "de-tex" algorithm woudl lead to a higher number of aligned sentences, or a higher quality of alignment. 

Because LaTeX source documents are typically organized into sections, macro alignment was performed by matching sections to each other using Levenstein distance between section titles. 

Once text was extracted and sections aligned, Stanford's CoreNLP tokenizer was used to tokenize sentences. Because the tokenizer is designed to work with English sentences, LaTeX syntax caused problems. 

```
"We now scale time $t$ by $\\tilde{\\alpha}^{-1}$ and the DW center velocity $\\dot{z}_c$ by $v_s=j_s/\\rho_s$: define $V_{_{\\mathrm{DW}}}\\equiv\\dot{z}_c\\rho_s/j_s$ and $\\tilde{t}\\equiv\\tilde{\\alpha}t$, then eliminate $\\varphi$ in Eq.",
      
"[\\[eq:DWeom\\]](#eq:DWeom){reference-type=\"eqref\" reference=\"eq:DWeom\"} we obtain the following formula $$\\begin{aligned} \\ddot{V}_{_{\\mathrm{DW}}}+2\\dot{V}_{_{\\mathrm{DW}}}+(G^2+1)V_{_{\\mathrm{DW}}}=G^2, \\label{eq:HO}\\end{aligned}$$ where $G=\\rho_s\\mathcal{G}/\\tilde{\\alpha}$.",

"Eq.",

"[\\[eq:HO\\]](#eq:HO){reference-type=\"eqref\" reference=\"eq:HO\"} represents the dynamics of a damped harmonic oscillator driven by a constant force.",
```

Multiple aligning algorithms were evaluated for the best alignment: MASSalign [@paetzold-etal-2017-massalign], a weighted longest common subsequence (described by [@tan+lee:14] and inspired by [@barzilay+elhadad:03]), and a Neural CRF aligner [@jiang:20].

TODO: Need to create a table of results here



## Evaluation



## Analysis

In some instances, the meaning of the sentence is changed deliberately: 

v1: We use all frames from one repetition of each action for training, and every 64$^{th}$ frame from all repetitions at test.

v2: We use all frames from one of the two instances of each action for training, and every 64$^{th}$ frame from all instances for testing.






## Conclusion
