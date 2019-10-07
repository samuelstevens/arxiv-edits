# Flow

1. Find all papers with different versions => `P: List[paperIDs]`
   - **persistent storage**
   - < 2M records
   - Use SQLite3

## For p in `P`:

1. Download all versions, unzip them, find the .tex src => `v: List[.tex src]`

2. Macro align based on section headers and extract text => `s: List[List[v1 text, v2 text, ...]]`
3. Turn section text into sentences (store sentences **persistently**)
   - NLTK
   - Stanford
   - Some combination?
4. Micro align sentences
   - idf weighted LCS (**need large corpus of documents for idf**)
   - alternative algorithm involving matrices (**need to read paper**)
5. Write sentence edits to **persistent storage**.

## Processes

### P1 - Getting Versioned Papers [DONE]

### Pn1 - For each `paperID` that has 2+ versions [Done for 15 papers]

### Pn2 - For each `paperID` that has 2+ versions (once all documents are tokenized)
