---
geometry: margin=1in
fontsize: 12pt
linestretch: 1.8
---

<!-- Title Page -->

# Using `arxiv.org` as a Source of Edit Data

Samuel Stevens

Janueary 2020

Computer Science Engineering

Prof. Wei Xu

## Abstract
- Abstract
  - summary of problem statement, objectives and methodology

\newpage
<!-- Body -->
<!-- 6 page maximum -->
<!-- Figures can be embedded or on single page at the end (included in 6 page max.) -->

## 1. Background and Motivation

<!-- define problem statement and general area in which you are working -->
Natural language processing has current applications in areas such as virtual assistants (Alexa, Siri), but also is applicable in machine translation (Google Translate) and automatic editing (Grammarly). Automatic editing results can be improved with additional examples of edits from which algorithms can learn. However, compared to web chats, translated texts, or free form prose, finding large repositories of text being edited (with before and after data) is more difficult. 

<!-- Include specific key facts about the problem at hand -->
`arxiv.org` is the "the standard repository for new papers in mathematics, physics, statistics, computer science, biology, and other disciplines" [Krant citation from Chenhao]. As noted in [chenhao citation], `arxiv.org` authors often submit multiple versions of their papers. At the time of writing, `arxiv.org` hosts 1.6M papers, with 611K with two or more versions. Can these papers be used to create a large dataset of examples of improving the quality of a sentence through editing? More concretely, can data from `arxiv.org` be used to improve current NLP metrics such as Split and Rephrase [CITATION NEEDED] or atomic insertions [WikiAtomicEdits citation here]?

### Related Work
<!-- Discuss previous related research in this area -->
<!-- assess the shortcomings with existing knowledge and/or existing approach -->
Previous work on using publicly available data for as a source of edit data has primarily focused on using Wikipeida [wikiatomicedits, wikisplit] (Chenhao has lots of sources here). `arxiv.org` has only been looked at by [Chenhao citation], examined all papers from 2011. Work on `arxiv.org` [Chenhao citation] and Wikipedia [WikiAtomicEdit citation] produced a dataset of 108,678 and 43 million sentence edits, respectively. I will look at all papers on `arxiv.org` with two or more revisions to create a larger dataset. In addition, [chenhao citation] does not look at how edit data in academic writing could improve model scores in areas such as Split and Rephrase [split and rephrase citation] or phrases insertion with existing sentences [wiki atomic edits citation]. Given that Wikipedia edit data has been useful in many applications including (...big list here [with citations]...), `arxiv.org` could also be a valuable source of edit data with many similar applications.


- Significance
  - discuss importances of research project. (seems quite similar to the previous point)

## Significance

- Research Goals
  - discuss hypotheses of project and/or overall objectives
  - include what you hope to resolve after performing this research
  - if working in a research group with multiple investigators, indicate your individual contribution to the project

## Research Goals

Using `arxiv.org` as a source of data could improve current NLP models in previously established natural language edit metrics such as Split and Rephrase [citation here] or Inserting a Phrase [wikiatomicedits citation]. I will be working on this project with Prof. Wei Xu as my research advisor and Chao Jiang, a Ph.D. student at Ohio State.

## Methodology

In order to use `arxiv.org` as a source of data, the papers availabe for download will be used as a source of academic writing. By finding papers with two or more versions, we can find edits made to papers and used as a source of data similar to WikiAtomicEdits [citation] or the Academic Edits dataset [chenhao citation]. 

### Finding Papers

To find papers, `arxiv.org`'s Open Archives Initiative for metadata harvesting will be used.

### Downloading Latex Source Code

To download the Latex source code, an automated web scraper will be developed using Python3. About 900K papers need to be downloaded. To not overly stress the `arxiv.org` server, a small delay will be introduced between requests. With this delay, it will require about 20 days to download all papers.

<!-- 
2 second(s)

900000 * 2 / 60 / 60 / 24 = 20.83 days

Produces how many days are required to download them all.

-->

<!-- Could rewrite and condense a lot of this into Gathering Data and Evaluating Models -->
### Converting Latex to Text

Because Latex is not a language with plain English text throughout, some processing is needed to extract the text from Latex. Several open source, free-to-use tools are available for extracting text from Latex. A tool will be chosen through the following process:

1. Extract the text from 5 documents using each of the potential tools.
2. Compare the tools' outputs with the final, true PDF document.
3. Aggregate the types and counts of errors made by each of the potential tools.
4. Select the tool with the best output. 
5. Fix the most common errors previously seen.
6. Extract text from an additional 3 documents using v2 of the selected tool. 
7. Compare the tool's output with v1 and the other original potential tools.
8. Aggregate the types and counts of errors made by each of the potential tools.
9. Fix errors until the selected tool does not make any errors not made by other candidates.

### Tokenization

To convert the raw text from the papers to sentences, Stanford's CoreNLP tokenizer will be used [citation]. A wrapper for said tokenizer was written by Chao Jiang [citation] which will be used to interface with Stanford's code. 

### Alignment

To align non-identical sentences, a variety of models will be evaluated against a gold standard that is manually aligned. 

### Using Alignments in Models

After creating a dataset of aligned sentences, the data will be used in different models to evaluate how additional data could improve already existing models/metrics.

## Timeline

\begin{tabular} { l l l }
Task & Start Date & End Date \\ \hline

Proposal & Jan 16, 2020 & Feb 14, 2020 \\

Gathering data & Jan 18, 2020 & Jan 27, 2020 \\

Taking 4999H (2nd session) & Feb 26, 2020 & Apr 20, 2020 \\

Evaluating models & Mar 2, 2020 & Apr 5, 2020 \\

Writing conference paper & Apr 6, 2020 & May 10, 2020 \\

Paper submission to EMNLP & May 11, 2020 & \\ \hline

\emph{Summer break} & & \\ \hline

Taking 4999H & Aug 25, 2020 & Dec 9, 2020 \\

Writing Ohio State thesis & Aug 25, 2020 & Sep 25, 2020 \\

Oral defense & Oct, 2020 & \\

Submission to Knowledge Bank & Oct, 2020 (after defense) & \\

Presenting at research forum & Nov, 2020 & \\ \hline

\end{tabular}

## Personal Statement

<!-- why do i want to work on this project?
* interesting
* want to see what research is like
* don't know if I want to go to grad school
* good practice in programming
* good project to spend time on
* new experience in writing a research paper to defend my thoughts
* learn from people who are smarter than me on a real project
* learn about a domain that seems really inaccessible to me
* work on brand new problem
* meet new people

3 main points:
1. working in this lets me learn a lot, from smarter, more experienced people 
2. apply material taught in my classes, in a domain that is difficult to get into.
3. I want to try research to see if i want to go to grad school -->

I am a third year Honors CSE student interested in artificial intelligence. Communicating with machines through natural language has been a challenge for researchers since the very start of AI research with the Turing test. The opportunity to work in NLP with Prof. Xu is unlike any experience I've had in industry internships. I'll be able to work with both current and future Ph.D.'s in a one-on-one setting on real project. I can't get that kind of experience anywhere else. Because this work is so different to what I experience in the classroom or in industry, I will learn more, and faster.

In addition, this project gives me an opportunity to apply the material taught in my AI and NLP classes in a real world project. So much of computer science is well-documented and freely available online. Since NLP and AI are the cutting edge of computer science, they aren't as accessible to a student like me. The opportunity to work on a real project with the best of the best isn't something I can find on a video tutorial

Finally, working on a research project from start to finish will give me an first-person look into the lives of Ph.D. students. This opportunity will help inform my decision about graduate school and doing research in my future career.

\newpage
<!-- Bibliography -->
- List all references (should also be cited throughout the body)

## References