---
geometry: "margin=1in"
fontsize: 12pt
linestretch: 1.8
bibliography: proposal.bib
reference-section-title: References
papersize: letter
title: Using arXiv as a Source of Edit Data (Undergrad Research in CSE)

author: 
  - Samuel Stevens
  - Prof. Wei Xu
date: February 2020

classoption:

abstract:
  Natural language processing (NLP) has real world applications in automatic editing software, such as Grammarly. Current models depend heavily on large quantities of data. Additional sources of domain specific data is important for improving current results. Past work has focused primarily on Wikipedia as a source of sentence-level edits. In this proposal, we describe how we plan to provide a new large scale (2M+) dataset of *academic* sentence-level edits from arXiv via text extraction and automatic sentence alignment, taking advantage of recently developed methods. In addition to creating a public dataset, we aim to perform introductory analysis to aid future research.
  # Abstract
  # summary of problem statement, objectives and methodology 
---

<!-- Title Page -->
\newpage

<!-- Body -->
<!-- 6 page maximum -->
<!-- Figures can be embedded or on single page at the end (included in 6 page max.) -->

## Background and Motivation

<!-- define problem statement and general area in which you are working -->
Natural language processing (NLP) has popular real world applications in areas such as virtual assistants (Alexa [^alexa], Siri [^siri]) and machine translation (Google Translate [^translate]), but also is applicable in automatic editing (Grammarly [^grammarly]). NLP model results can be improved with additional examples from which they can learn. However, compared to web chats or translated documents (for Alexa/Siri or Google Translate, respectively), finding large datasets of edited text (with "before" and "after" text) is more difficult. 

[^alexa]: https://www.amazon.com/b?node=17934671011
[^siri]: https://www.apple.com/siri/
[^translate]: https://translate.google.com/
[^grammarly]: https://www.grammarly.com/

<!-- Include specific key facts about the problem at hand -->
arXiv is the "the standard repository for new papers in mathematics, physics, statistics, computer science, biology, and other disciplines" [@krantz]. As noted by @chenhao, arXiv authors often submit multiple versions of their papers. At the time of writing, arXiv hosts 1.6M papers, with 611K with two or more versions. We propose that these papers can be used to create a large (2M+ sentences) dataset of examples of improving the quality of a sentence through editing. More concretely, we propose that data from arXiv can be used to improve NLP edit metrics such as identifying sentences that need editing [@aesw].

### Related Work
<!-- Discuss previous related research in this area -->
<!-- assess the shortcomings with existing knowledge and/or existing approach -->
Previous work on using publicly available data for as a source of edit data has primarily focused on using Wikipedia [@wikiatomicedits; @wikisplit]. @chenhao looked at arXiv and examined all papers from 2011. Work on arXiv and Wikipedia [@wikiatomicedits] produced a dataset of 108,678 and 43 million sentence edits, respectively. In addition, @chenhao use sentence-level edits to study statement strength. 

Work looking at edits in academic domains [@aesw] used data from a professional editing company (VTeX [^vtex]) to create a dataset of sentence-level edits in academic writing. 

[^vtex]: http://www.vtex.lt

We propose looking at all papers on arXiv with two or more revisions to create a large, general purpose dataset. 

## Significance
<!-- discuss importances of research project -->
Given that Wikipedia edit data has been useful in many applications including sentence compression [@yamangil], spelling correction [@zesch], Split and Rephrase [@wikisplit] and generating insertion phrases [@wikiatomicedits], arXiv could also be a valuable source of edit data with many similar applications. By introducing a dataset of academic writing, we will be able to perform similar tasks in more formal genres, such as writing and editing scientific papers.

Due the to this data's relative novelty, part of this project's significance is discoving novel qualities and features that can be utilized by future work. 


## Research Goals
<!-- discuss hypotheses of project and/or overall objectives -->
<!-- include what you hope to resolve after performing this research -->
We aim to produce a dataset of more than 2 million sentence-level edits in an academic writing domain, as well an initial analysis on distinctive features of this new dataset. 

<!-- if working in a research group with multiple investigators, indicate your individual contribution to the project -->
I will be working on this project with Chao Jiang, a Ph.D. student at Ohio State and Prof. Wei Xu as my research advisor. Given Jiang and Prof. Xu's experience in sentence alignment [@newsela], my role will be to design a pipeline for extracting plain text from documents stored on arXiv and to further the analysis of aligned sentences.

## Methodology

To extract data from arXiv, we will analyze all papers with two or more versions available. From these *version pairs*, we can find changes made to papers and then break them down into sentence-level edits.

### Finding Papers

To find papers with two or more versions, arXiv's Open Archives Initiative (OAI) protocol for metadata harvesting will be used.

### Downloading Latex Source Code

To download the Latex source code, an automated web scraper will be developed using Python. About 1.5M papers need to be downloaded. To not overly stress the arXiv server, a small delay will be introduced between requests. With this delay, it will require about 10 days to download every paper.

<!-- 
3 second(s)

900000 * 3 / 60 / 60 / 24 = 31.25 days

Produces how many days are required to download them all.

-->

<!-- Could rewrite and condense a lot of this into Gathering Data and Evaluating Models -->
### Converting Latex to Text

Because Latex is a markup language, rather than plain English text, some processing is needed to extract the text from Latex. Several open source, free-to-use tools (Pandoc[^pandoc], opendetex[^opendetex]) are available for extracting text from Latex. A tool will be chosen or developed to accurately extract plain English text from Latex source documents.

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

To convert the plain English text from the papers to sentences, Stanford's CoreNLP software will be used [@stanfordnlp]. A wrapper for said software written by Jiang will be used to interface with Stanford's code. 

### Alignment

To align non-identical sentences, we will take advantage of Jiang's recent experience in sentence alignment and evaluate several approaches to alignment. Due to the limited number of edits between documents, alignment is not expected to be a extremely difficult task.

### Analysis

Because arXiv is a relatively unexplored dataset, we will perform some linguistic analysis on the data, similar to @diyi. This could include a general overview, edit type classification, edit intention and a comparison with similar, existing datasets.

## Timeline

\begin{tabular} { l l l }
Task & Start Date & End Date \\ \hline

Proposal & Jan 16, 2020 & Feb 14, 2020 \\

Gathering data & Jan 18, 2020 & Jan 27, 2020 \\

Analyzing data & Jan 28, 2020 & Mar 15, 2020 \\

Taking 4999H (2nd session) & Feb 26, 2020 & Apr 20, 2020 \\

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

I am a third year Honors CSE student interested in artificial intelligence. Communicating with machines through natural language has been a challenge for researchers since the very start of AI research with the Turing test. The opportunity to work in NLP with Prof. Xu is unlike any previous experience I've had; I'll be able to work with both current and future Ph.D.'s in a one-on-one setting on real project. I can't get that kind of experience anywhere else. Because this work is so different to what I experience in the classroom or the workforce, I will learn more, and faster.

In addition, this project gives me an opportunity to apply the material taught in my AI and NLP classes in a real world project. So much of computer science is well-documented and freely available online. Since NLP and AI are the on cutting edge of computer science, they aren't as accessible. The opportunity to work on a real NLP project with the best of the best isn't widely available, and I want to take advantage of it while I attend Ohio State.

Finally, working on a research project from start to finish will give me an first-person look into the lives of Ph.D. students. This opportunity will help inform my decision about graduate school and research in my future.

\newpage
<!-- Bibliography -->
<!-- List all references (should also be cited throughout the body) -->

## References