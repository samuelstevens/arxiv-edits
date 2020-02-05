---
geometry: margin=1in
fontsize: 12pt
linestretch: 1.8
bibliography: proposal.bib
reference-section-title: References
---

<!-- Title Page -->

# Using `arxiv.org` as a Source of Edit Data

Samuel Stevens

February 2020

Computer Science Engineering

Prof. Wei Xu

## Abstract
<!-- Abstract -->
<!-- summary of problem statement, objectives and methodology -->

Natural language processing (NLP) has applications in automatic editing applications, such as Grammarly. Because current models are so heavily data-driven, additional source of data for specific problems can dramatically improve current results. We aim to provide a new large scale dataset of sentence-level edits from `arxiv.org` via text extraction and automatic sentence alignment, taking advantage of recently developed methods. In addition to a dataset of sentence-level edits, we aim to provide some introductory analysis of the data to aid future research. 

\newpage
<!-- Body -->
<!-- 6 page maximum -->
<!-- Figures can be embedded or on single page at the end (included in 6 page max.) -->

## 1. Background and Motivation

<!-- define problem statement and general area in which you are working -->
Natural language processing has current applications in areas such as virtual assistants (Alexa [^alexa], Siri [^siri]), but also is applicable in machine translation (Google Translate [^translate]) and automatic editing (Grammarly [^grammarly]). Automatic editing results can be improved with additional examples of edits from which algorithms can learn. However, compared to web chats, translated texts, or free form prose, finding large repositories of text being edited (with before and after data) is more difficult. 

[^alexa]: https://www.amazon.com/b?node=17934671011
[^siri]: https://www.apple.com/siri/
[^translate]: https://translate.google.com/
[^grammarly]: https://www.grammarly.com/

<!-- Include specific key facts about the problem at hand -->
`arxiv.org` is the "the standard repository for new papers in mathematics, physics, statistics, computer science, biology, and other disciplines" [@krantz]. As noted in [@chenhao], `arxiv.org` authors often submit multiple versions of their papers. At the time of writing, `arxiv.org` hosts 1.6M papers, with 611K with two or more versions. Can these papers be used to create a large dataset of examples of improving the quality of a sentence through editing? More concretely, can data from `arxiv.org` be used to improve current NLP metrics such as Split and Rephrase [@splitandrephrase] or atomic insertions [@wikiatomicedits]?

### Related Work
<!-- Discuss previous related research in this area -->
<!-- assess the shortcomings with existing knowledge and/or existing approach -->
Previous work on using publicly available data for as a source of edit data has primarily focused on using Wikipeida [@wikiatomicedits; @wikisplit] (Chenhao has lots of sources here). `arxiv.org` has only been looked at by @chenhao, examined all papers from 2011. Work on `arxiv.org` [@chenhao] and Wikipedia [@wikiatomicedits] produced a dataset of 108,678 and 43 million sentence edits, respectively. I will look at all papers on `arxiv.org` with two or more revisions to create a larger dataset. In addition, [@chenhao] does not look at how edit data in academic writing could improve model scores in areas such as Split and Rephrase [@splitandrephrase] or phrases insertion with existing sentences [@wikiatomicedits]. Given that Wikipedia edit data has been useful in many applications including (...big list here [with citations]...), `arxiv.org` could also be a valuable source of edit data with many similar applications.

## Significance
<!-- discuss importances of research project -->
Previous work on edit data has demonstrated that edit data can be used for both discriminative [@wikisplit; @wikiatomicedits] and generative [@wikiatomicedits] tasks. By introducing a dataset of academic writing, we will be able to perform similar tasks in more formal domains, such as writing and editing scientific papers.

Due the to the lack of understanding about this data, part of the significance of this project is discoving unique features that can be utilized by future work. 


## Research Goals
<!-- discuss hypotheses of project and/or overall objectives -->
<!-- include what you hope to resolve after performing this research -->
At the end of this project, we aim to produce a large dataset of sentence level edits, deletions and additions in an academic writing domain, as well an initial analysis on distinctive features of this new dataset. 

<!-- if working in a research group with multiple investigators, indicate your individual contribution to the project -->
I will be working on this project with Prof. Wei Xu as my research advisor and Chao Jiang, a Ph.D. student at Ohio State. Given Prof. Xu and Chao Jiang's experience in sentence alignment, my role will be to design a pipeline for extracting plain text from documents stored on `arxiv.org` and furthering the analysis of aligned sentences.

## Methodology

In order to use `arxiv.org` as a source of data, the papers availabe for download will be used as a source of academic writing. By finding papers with two or more versions, we can find edits made to papers and used as a source of data similar to WikiAtomicEdits [@wikiatomicedits] or the Academic Edits dataset [@chenhao]. 

### Finding Papers

To find papers, `arxiv.org`'s Open Archives Initiative for metadata harvesting will be used.

### Downloading Latex Source Code

To download the Latex source code, an automated web scraper will be developed using Python. About 900K papers need to be downloaded. To not overly stress the `arxiv.org` server, a small delay will be introduced between requests. With this delay, it will require about 10 days to download all papers.

<!-- 
3 second(s)

900000 * 3 / 60 / 60 / 24 = 31.25 days

Produces how many days are required to download them all.

-->

<!-- Could rewrite and condense a lot of this into Gathering Data and Evaluating Models -->
### Converting Latex to Text

Because Latex is not a language with plain English text throughout, some processing is needed to extract the text from Latex. Several open source, free-to-use tools (Pandoc[^pandoc], opendetex[^opendetex]) are available for extracting text from Latex. A tool will be chosen or developed to accurately extract plain English text from Latex source documents.

[^pandoc]: https://pandoc.org/
[^opendetex]: https://github.com/pkubowicz/opendetex
<!-- 1. Extract the text from 5 documents using each of the potential tools.
2. Compare the tools' outputs with the final, true PDF document.
3. Aggregate the types and counts of errors made by each of the potential tools.
4. Select the tool with the best output. 
5. Fix the most common errors previously seen.
6. Extract text from an additional 3 documents using v2 of the selected tool. 
7. Compare the tool's output with v1 and the other original potential tools.
8. Aggregate the types and counts of errors made by each of the potential tools.
9. Fix errors until the selected tool does not make any errors not made by other candidates. -->

### Sentence Splitting

To convert the raw text from the papers to sentences, Stanford's CoreNLP software will be used [@stanfordnlp]. A wrapper for said software written by Chao Jiang will be used to interface with Stanford's code. 

### Alignment

To align non-identical sentences, we will take advantage of Chao Jiang's recent experience in sentence alignment and evaluate several approaches to alignment. Because of the limited number of edits between documents, alignment is not expected to be a extremely difficult task.

### Analysis

Because `arxiv.org` is a relatively unexplored dataset, we will perform some linguistic analysis on the data, similar to [@diyi]. This might include edit type classification, edit intention, or something further. 

## Timeline

\begin{tabular} { l l l }
Task & Start Date & End Date \\ \hline

Proposal & Jan 16, 2020 & Feb 14, 2020 \\

Gathering data & Jan 18, 2020 & Jan 27, 2020 \\

Taking 4999H (2nd session) & Feb 26, 2020 & Apr 20, 2020 \\

Analyzing data & Jan 28, 2020 & Mar 15, 2020 \\

Writing conference paper & Mar 16, 2020 & May 10, 2020 \\

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
<!-- List all references (should also be cited throughout the body) -->

## References