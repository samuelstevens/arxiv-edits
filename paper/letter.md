---
geometry:
- margin=1.5in
---

<!-- 
pandoc --from markdown --to pdf --standalone --out paper/letter.pdf paper/letter.md

pandoc --from markdown --to docx --standalone --out paper/letter.docx paper/letter.md
pandoc --from markdown --to latex --standalone --out paper/letter.tex paper/letter.md

 -->

To whom it may concern,

 I am writing to support Sam Stevens' decision to pursue an undergraduate honors thesis in my research lab. 

<!-- Context for the research project and a discussion of why the research is significant; -->

My main research focus is in natural language processing and machine learning. To achieve state of the art results, I take advantage of large data to model language semantics. Different types of data provide different semantics. With Sam's research project, we aim to model edit semantics--the changes betweens documents. We need a large number of examples of edits made to documents to learn why an edit was made and how a sentence was changed. Sam's research project is focused on gathering this large quantity of data from arXiv[^arxiv], an online repository of research papers.

<!-- Description of how the proposed project fits within other related research projects in your lab; -->

I look at natural language generation as a sequence to sequence problem, using existing machine translation frameworks with large scale datasets to achieve state-of-the-art performance. Sam's project's immediate goal is to create a large scale dataset that could be used to train a machine translation model to produce higher quality sentences from never-seen-before input.

[^arxiv]: https://arxiv.org/

With the data Sam aims to gather, we can look into why a sentence is edited, how best to change a sentence or what words are most appropriate for a given topic. 

<!-- Description of how the research work will be supervised (e.g., weekly meetings or by a graduate/postdoctoral student); -->

Sam will work with Chao Jiang, a 2nd year Ph.D. student who I advise. The three of us will meet weekly.

<!-- If student is working in a research group with multiple investigators, indicate his or her individual contribution to the project; -->

Sam will be responsible for the extraction of sentences from papers on arXiv. He will also perform an initial analysis of the dataset, which might include a general overview, edit type classification, edit intention classification and/or a comparison with similar, existing datasets.

<!-- A discussion of the ability of the student to successfully carry out the project  -->

When Sam first asked to work with me in the autumn of 2019, I asked him to develop software to download a large amount of data from Urban Dictionary[^urbandict]. He did so with vigor and produced a high quality Python 3 package with documentation and examples. In addition, Sam's GPA and work experience are outstanding, and his previous experience in software engineering will allow him to focus on research without being stopped by technical issues.

[^urbandict]: https://www.urbandictionary.com/

<!-- A description of progress made up to the current time, if the student has already started the proposed research project; -->
Sam started on this project in October, 2019. Since then, he has developed a program to download the papers from arXiv and extract individual sentences from their Latex source code. In addition, he and Chao started developing a sentence alignment algorithm and analyzing initial data.

<!-- A description of previous research, if the student has worked on other research projects under your supervision; -->

<!-- A discussion of the proposed time schedule and whether the project can be completed in the given time; -->

Given the specific scope of Sam's project, I am confident that he will complete the project in time. Because we aim to submit this paper to EMNLP 2020, focusing our effort on final results will be critical. However, both Sam's GPA and previous work experience indicate that he is able to work under pressure and produce high-quality results.

Sincerely,

Wei Xu