"""Text embedders for dense retrieval.

Two implementations behind one interface:

- `SentenceTransformerEmbedder` — the production embedder, a local Hugging Face
  `sentence-transformers` model. Free, no API key, runs on CPU. Heavy deps
  (torch), so it is imported lazily and lives in `requirements-ml.txt`, not the
  base image.
- `HashingEmbedder` — a deterministic, dependency-light embedder (numpy only).
  Not semantically meaningful; it exists so tests and CI can exercise the full
  embed -> store -> retrieve path without downloading a model.

Both return unit-normalized vectors so a dot product equals cosine similarity.
"""

from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...
    def embed(self, texts: list[str]) -> np.ndarray: ...  # shape (len(texts), dim), L2-normalized


def _l2_normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


class HashingEmbedder:
    """Hashing-trick embedder: deterministic, fast, no model download.

    Tokenizes on whitespace and hashes tokens into a fixed-width vector. Good
    enough to prove the retrieval plumbing and to give tests stable vectors;
    it is NOT a substitute for a real semantic embedder in production.
    """

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self._dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in text.lower().split():
                h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:8], "little")
                out[i, h % self._dim] += 1.0
        return _l2_normalize(out)


class SentenceTransformerEmbedder:
    """Local Hugging Face sentence-transformers embedder (production default).

    Default model `BAAI/bge-small-en-v1.5` (384-dim) is a strong, small,
    CPU-friendly general retriever. For a biomedical-specific upgrade, swap in a
    PubMedBERT/SPECTER2 sentence model — keep `dim` in sync with db/schema.sql.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        # Imported here so the base image and demo backend never pull in torch.
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vecs = self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )
        return vecs.astype(np.float32)


def build_embedder(kind: str, model_name: str, dim: int) -> Embedder:
    if kind == "hashing":
        return HashingEmbedder(dim=dim)
    if kind == "sentence-transformer":
        return SentenceTransformerEmbedder(model_name=model_name)
    raise ValueError(f"unknown embedder kind: {kind!r}")
