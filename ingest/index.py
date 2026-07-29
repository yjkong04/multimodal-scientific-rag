"""Embed chunks and write them into pgvector.

Upserts a parsed paper and its chunks into the papers / text_chunks / figures
tables (see db/schema.sql), embedding text-chunk content and figure captions
with the given embedder. Idempotent per paper: an existing paper's chunks are
replaced so re-ingesting is safe.
"""

from __future__ import annotations

from api.embeddings import Embedder
from .chunk import Chunk
from .pmc import ParsedPaper


def write_paper(conn, paper: ParsedPaper, chunks: list[Chunk], embedder: Embedder) -> tuple[int, int]:
    """Write one paper's chunks to pgvector. Returns (n_text, n_figures)."""
    from pgvector.psycopg import register_vector

    register_vector(conn)

    text_chunks = [c for c in chunks if c.modality == "text"]
    figures = [c for c in chunks if c.modality == "figure"]

    text_vecs = embedder.embed([c.content for c in text_chunks]) if text_chunks else []
    fig_vecs = embedder.embed([c.content for c in figures]) if figures else []

    with conn.transaction():
        conn.execute(
            """
            INSERT INTO papers (paper_id, title)
            VALUES (%s, %s)
            ON CONFLICT (paper_id) DO UPDATE SET title = EXCLUDED.title
            """,
            (paper.paper_id, paper.title),
        )
        # Replace existing chunks so re-ingest is idempotent.
        conn.execute("DELETE FROM text_chunks WHERE paper_id = %s", (paper.paper_id,))
        conn.execute("DELETE FROM figures WHERE paper_id = %s", (paper.paper_id,))

        for c, vec in zip(text_chunks, text_vecs):
            conn.execute(
                """
                INSERT INTO text_chunks (chunk_id, paper_id, section, ord, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (c.chunk_id, c.paper_id, c.section, c.ord, c.content, vec),
            )
        for c, vec in zip(figures, fig_vecs):
            conn.execute(
                """
                INSERT INTO figures
                    (figure_id, paper_id, section, figure_label, caption, image_uri, caption_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (c.chunk_id, c.paper_id, c.section, c.figure_label, c.content, None, vec),
            )

    return len(text_chunks), len(figures)
