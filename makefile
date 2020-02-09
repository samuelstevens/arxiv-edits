CC=gcc
CFLAGS="-std=c99" "-pedantic" "-Wall" "-O3"

all: arxivedits/lcsmodule/lcs.so

arxivedits/lcsmodule/lcs.so: arxivedits/lcsmodule/lcs.o
	$(CC) -shared -o arxivedits/lcsmodule/lcs.so arxivedits/lcsmodule/lcs.o

arxivedits/lcsmodule/lcs.o: arxivedits/lcsmodule/lcs.c
	$(CC) -c $(CLFAGS) -fpic arxivedits/lcsmodule/lcs.c -o arxivedits/lcsmodule/lcs.o

profile: arxivedits/lcsmodule/lcs.so
	python -m cProfile -o evaluate.py.prof arxivedits/evaluate.py

visualize: evaluate.py.prof
	snakeviz evaluate.py.prof

proposal: paper/proposal.md
	pandoc --from markdown+citations --bibliography=paper/proposal.bib --to pdf --filter pandoc-citeproc --standalone --number-sections --shift-heading-level-by=-1 --out paper/proposal.pdf paper/proposal.md


test: FORCE
	python -m pytest tests/



FORCE: