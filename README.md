# Arxiv Edits

## Installation

```bash
# clone and navigate to repo
git clone https://github.com/samuelstevens/arxiv-edits.git
cd arxiv-edits

# activate your python environment now
source ./venv/bin/activate

# install MASSAlign
git clone https://github.com/samuelstevens/massalign.git
cd massalign
python setup.py install

# install other dependencies
cd ../arxivedits # or however you get back to this project
pip install -r requirements.txt

# make sure you have pandoc installed
pandoc --version

# make sure you have sqlite3 installed
sqlite3 --version
```

### Java

To run the CoreNLP tokenizer, you need to edit the classpath in `tokenizer.py` to the location of your .jar

```python
self.classpath = '/Users/samstevens/Java/stanford-corenlp/*'
```

This path corresponds to this file structure:

[File Structure](docs/images/filestructure.png)

```bash
# You can now run the various scripts with:
python arxiv-edits/versions.py # etc
```

### Dependencies
* Python 3
* [MASSAlign for Python 3](https://github.com/samuelstevens/massalign)
* [Pandoc](https://pandoc.org/)
* [SQLite3](https://sqlite.org/index.html)
* [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/index.html#download)


## Gathering Data



