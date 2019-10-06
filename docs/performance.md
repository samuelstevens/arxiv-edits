# Performance

## Getting papers with multiple versions

Currently, takes about 50 seconds to query 100 papers.

With 1.6M papers on Arxiv:

`50 seconds / 100 papers \* 1.6M papers \* 1 hour / 3600 seconds \* 1 day / 24 hours = 9.25 days`

- Started at 16:00 30/9/2019
- Should finish around 22:00 9/10/2019 (10 PM next Wednesday).
- Will check progress at 22:00 30/9/2019 (6 hours), should be ~43,200 papers.

## NLTK vs Stanford

- Both Stanford and NLTK struggled with `Sec.` and `Fig.`, but since the NLTK package has python bindings, it's easier to rejoin the array than with Stanford's CLI interface.
