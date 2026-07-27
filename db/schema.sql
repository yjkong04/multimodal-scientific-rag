-- Schema for the pgvector-backed corpus (Week 2+).
-- The demo store does not use this; it's here so `docker compose up db` gives
-- you a ready database and to pin down the storage model early.
--
-- Embedding dimension is a placeholder (768) until the embedding model is
-- chosen in Week 2; adjust the vector(...) sizes to match.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS papers (
    paper_id   TEXT PRIMARY KEY,          -- e.g. a PMC id
    title      TEXT,
    source_url TEXT,
    license    TEXT,
    ingested_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS text_chunks (
    chunk_id  TEXT PRIMARY KEY,
    paper_id  TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    section   TEXT,
    ord       INT,                        -- position within the paper
    content   TEXT NOT NULL,
    embedding vector(768)
);

CREATE TABLE IF NOT EXISTS figures (
    figure_id    TEXT PRIMARY KEY,
    paper_id     TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    section      TEXT,
    figure_label TEXT,                     -- e.g. 'Figure 3'
    caption      TEXT,
    image_uri    TEXT,                      -- where the figure image is stored
    caption_embedding vector(768)
);

-- Cosine-distance indexes for retrieval. IVFFlat needs data present + ANALYZE
-- before it helps; fine to create empty and let Week 2 populate.
CREATE INDEX IF NOT EXISTS idx_text_chunks_embedding
    ON text_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_figures_caption_embedding
    ON figures USING ivfflat (caption_embedding vector_cosine_ops) WITH (lists = 100);
