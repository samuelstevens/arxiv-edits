Notes

Jan 29, 2020 - Looking at papers 1-20 (first impressions)

Detex problems
* newcommand and def need serious work in tex.py. part of the problem is that they need preprocessing and post processing. the preprocessing removes a lot of potential for error because it removes a great deal of text (figures, equations, etc). the postprocessing is necessary because the macros might add figures and equations back to the text.
* \newline needs to be turned to \n

Sentence splitting problems
* Split after [Math] <capital letter>?
* Split after Fig. <capital letter>? The same question applies for Sec., Ref., etc.

Data impressions
* papers have a pretty even split between:
  * many sentence level edits
  * large (>40%) rewrites
  * nearly no edits (at least in sentences, which doesn't include appendices, figures, etc)
* other papers:
  * moved sections around within a papers
  * changed numbers
* sentence level edits are often:
  * moving words within the same sentence
  * simplifying (thus, in essence -> thus)
  * improve the language (get -> obtain)

I think we can use identical sentences as anchors to help us align.

Possible metrics we could use to further measure initial impressions of the data
1. distribution of versions over all submissions
2. topic of paper vs average version count, version distribution, etc.
3. paper # for a given auther vs average version count, version distribution, etc. (harder because authors aren't as categorical as topics)
4. Python's difflib to find different sentences between versions. 
5. different sentences between 1->2, 2->3, etc.
6. breakdown of differences using difflib -> is the distribution skewed, or normal?
