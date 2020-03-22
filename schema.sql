CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    version_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS authors (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS categories (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS paperauthor (
    arxiv_id TEXT NOT NULL,
    author TEXT NOT NULL,
    FOREIGN KEY(arxiv_id) REFERENCES papers(arxiv_id),
    FOREIGN KEY(author) REFERENCES authors(name)
);

CREATE TABLE IF NOT EXISTS papercategory (
    arxiv_id TEXT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY(arxiv_id) REFERENCES papers(arxiv_id),
    FOREIGN KEY(category) REFERENCES authors(name)
);