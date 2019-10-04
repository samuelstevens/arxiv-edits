import nltk.data


class splitter:
    def __init__(self):
        self.detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def split(self, text):
        return self.detector.tokenize(text)
