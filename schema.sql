CREATE TABLE IF NOT EXISTS papers (
  arxiv_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS versions (
  arxiv_id TEXT NOT NULL,
  number INTEGER NOT NULL,
  time DATETIME,
  FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);

CREATE TABLE IF NOT EXISTS categories (
  arxiv_id TEXT NOT NULL,
  spec TEXT NOT NULL,
  PRIMARY KEY (arxiv_id, spec),
  FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);

CREATE TABLE IF NOT EXISTS authors (
  arxiv_id TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT NOT NULL,
  PRIMARY KEY (arxiv_id, first_name, last_name),
  FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);