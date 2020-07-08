import os, pickle, functools

from arxivedits import tokenizer, data

tok = tokenizer.CoreNLPTokenizer()

preprocess_filename = os.path.join(data.ALIGNMENT_DIR, "preprocess_sent_dict.pkl")

with open(preprocess_filename, "rb",) as global_file:
    preprocess_sent_dict = pickle.load(global_file)


def save_preprocess_sent_dict() -> None:
    with open(preprocess_filename, "wb") as file:
        pickle.dump(preprocess_sent_dict, file)


@functools.lru_cache(maxsize=512)
def preprocess_sent(sent: str) -> str:
    if not sent:
        return ""

    if sent.isspace():
        return ""

    if sent in preprocess_sent_dict:
        return sent

    processed = " ".join(tok.tokenize(sent).words())

    processed = (
        processed.replace("[ MATH ]", " [MATH] ")
        .replace("[ EQUATION ]", " [EQUATION] ")
        .replace("[ REF ]", " [REF] ")
        .replace("[ CITATION ]", " [CITATION] ")
    )  # TODO: shouldn't be hard-coded values

    processed = " ".join(processed.split())

    preprocess_sent_dict[sent] = processed

    return processed
