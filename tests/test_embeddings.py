"""Embedder tests. Pure/offline — no model download, no DB."""

import numpy as np

from api.embeddings import HashingEmbedder, build_embedder


def test_hashing_embedder_shape_and_dtype():
    e = HashingEmbedder(dim=384)
    v = e.embed(["heart rate variability", "another chunk"])
    assert v.shape == (2, 384)
    assert v.dtype == np.float32


def test_hashing_embedder_is_deterministic():
    e = HashingEmbedder(dim=128)
    a = e.embed(["same text here"])
    b = e.embed(["same text here"])
    assert np.allclose(a, b)


def test_embeddings_are_unit_normalized():
    e = HashingEmbedder(dim=256)
    v = e.embed(["some words to embed", "more words"])
    norms = np.linalg.norm(v, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_empty_string_embeds_to_zero_vector_without_error():
    e = HashingEmbedder(dim=64)
    v = e.embed([""])
    assert v.shape == (1, 64)
    assert np.allclose(v[0], 0.0)  # no tokens -> zero, normalization guarded


def test_build_embedder_selects_hashing():
    e = build_embedder("hashing", "unused", 384)
    assert isinstance(e, HashingEmbedder)
    assert e.dim == 384


def test_build_embedder_rejects_unknown():
    try:
        build_embedder("nope", "m", 384)
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown embedder kind")
