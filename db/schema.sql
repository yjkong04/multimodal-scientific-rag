-- Schema for the pgvector-backed corpus (Week 2+).
-- The demo store does not use this; it's here so `docker compose up db` gives
-- you a ready database and to pin down the storage model early.
--
-- Embedding dimension is 384, matching the default embedder
-- (BAAI/bge-small-en-v1.5). If you swap the model, update these vector(...)
-- sizes and api Settings.embedding_dim to match.

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
    embedding vector(384)
);

CREATE TABLE IF NOT EXISTS figures (
    figure_id    TEXT PRIMARY KEY,
    paper_id     TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    section      TEXT,
    figure_label TEXT,                     -- e.g. 'Figure 3'
    caption      TEXT,
    image_uri    TEXT,                      -- where the figure image is stored
    caption_embedding vector(384)
);

-- Cosine-distance HNSW indexes for retrieval. HNSW gives full recall out of the
-- box and needs no training data, so it is correct from the first row up to
-- large corpora -- unlike IVFFlat, whose lists/probes cold-start silently drops
-- results on a small table.
CREATE INDEX IF NOT EXISTS idx_text_chunks_embedding
    ON text_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_figures_caption_embedding
    ON figures USING hnsw (caption_embedding vector_cosine_ops);
