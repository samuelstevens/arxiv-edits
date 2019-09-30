CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    queried INTEGER NOT NULL,
    multiple_versions INTEGER NOT NULL
);