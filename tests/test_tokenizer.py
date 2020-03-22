from arxivedits import tokenizer


def test_split_on_tag():
    text = "First, [EQUATION] Another sentence."
    tag = "[EQUATION]"

    expected = ["First, [EQUATION]", "Another sentence."]

    assert tokenizer.split_on_tag(tag, text) == expected

    for sent in expected:
        assert tokenizer.split_on_tag(tag, sent) == [sent]


def test_split_on_tag_with_whitespace():
    text = "First, [EQUATION] \t Another sentence."
    tag = "[EQUATION]"

    expected = ["First, [EQUATION]", "Another sentence."]

    assert tokenizer.split_on_tag(tag, text) == expected

    for sent in expected:
        assert tokenizer.split_on_tag(tag, sent) == [sent]


def test_split_on_tag_with_no_whitespace():
    text = "First, [EQUATION]Another sentence."
    tag = "[EQUATION]"

    expected = ["First, [EQUATION]", "Another sentence."]

    assert tokenizer.split_on_tag(tag, text) == expected

    for sent in expected:
        assert tokenizer.split_on_tag(tag, sent) == [sent]


def test_split_on_multiple_tag():
    text = "First, [EQUATION]Another sentence with [EQUATION] Then another."
    tag = "[EQUATION]"

    expected = [
        "First, [EQUATION]",
        "Another sentence with [EQUATION]",
        "Then another.",
    ]

    assert tokenizer.split_on_tag(tag, text) == expected

    for sent in expected:
        assert tokenizer.split_on_tag(tag, sent) == [sent]


def test_join_sentences():
    sentences = ["In Fig.", "1, you can see this."]

    expected = ["In Fig. 1, you can see this."]

    assert tokenizer.join_sentences_wrapper(sentences) == expected

    for sentence in expected:
        assert tokenizer.join_sentences_wrapper([sentence]) == [sentence]
