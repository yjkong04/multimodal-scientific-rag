"""Evaluation harness (Week 5).

Measures the system instead of eyeballing it, across three axes:

- retrieval quality (recall@k, MRR) against gold source ids,
- groundedness (inline-citation support + citation-set precision/recall vs gold),
- refusal correctness (does it refuse exactly when the corpus can't answer).

The metric functions are pure and store/generator-agnostic; the harness wires
them to any `Store` + `Generator`, so the same code scores the demo backend, the
pgvector corpus, and each candidate VLM in the comparison sweep.
"""
