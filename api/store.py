"""Retrieval store abstraction + an in-memory demo implementation.

The store is the seam between retrieval and the rest of the app. Week 1 ships
`DemoStore` so the API returns a real, cited response shape with zero setup.
Week 2 adds a `PgVectorStore` behind the same `Store` protocol and the app
switches on `settings.store_backend` — no changes to the API layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from .schemas import Modality


@dataclass
class Record:
    """One retrievable unit: a text chunk or a figure."""

    paper_id: str
    source_id: str
    modality: Modality
    text: str  # chunk text, or figure caption
    section: str | None = None
    figure_label: str | None = None
    image_uri: str | None = None  # populated for figures from Week 3


@dataclass
class ScoredRecord:
    record: Record
    score: float


class Store(Protocol):
    def search_text(self, query: str, k: int) -> list[ScoredRecord]: ...
    def search_figures(self, query: str, k: int) -> list[ScoredRecord]: ...
    @property
    def name(self) -> str: ...


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(s: str) -> list[str]:
    return _TOKEN.findall(s.lower())


def _overlap_score(query: str, text: str) -> float:
    """Cheap lexical overlap. Stand-in for dense similarity until Week 2.

    Real embeddings replace this; the interface (query, text) -> score stays.
    """
    q = set(_tokenize(query))
    if not q:
        return 0.0
    t = _tokenize(text)
    if not t:
        return 0.0
    hits = sum(1 for tok in t if tok in q)
    return hits / (len(t) ** 0.5)  # length-normalized so long chunks don't dominate


@dataclass
class DemoStore:
    """A tiny hand-built corpus so the API works end to end with no DB.

    The content is synthetic and generic on purpose — it exists to exercise
    text + figure retrieval and the citation shape, not to be real science.
    """

    records: list[Record] = field(default_factory=list)

    @property
    def name(self) -> str:
        return "demo"

    def __post_init__(self) -> None:
        if not self.records:
            self.records = _demo_records()

    def _search(self, query: str, k: int, modality: Modality) -> list[ScoredRecord]:
        scored = [
            ScoredRecord(r, _overlap_score(query, r.text))
            for r in self.records
            if r.modality == modality
        ]
        scored = [s for s in scored if s.score > 0]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]

    def search_text(self, query: str, k: int) -> list[ScoredRecord]:
        return self._search(query, k, Modality.TEXT)

    def search_figures(self, query: str, k: int) -> list[ScoredRecord]:
        return self._search(query, k, Modality.FIGURE)


def _demo_records() -> list[Record]:
    pid = "DEMO-0001"
    return [
        Record(
            paper_id=pid,
            source_id=f"{pid}:c1",
            modality=Modality.TEXT,
            section="Methods",
            text=(
                "Samples were treated with the compound across a dose series and "
                "response was measured after 48 hours using a standard viability assay. "
                "Each condition was run in triplicate."
            ),
        ),
        Record(
            paper_id=pid,
            source_id=f"{pid}:c2",
            modality=Modality.TEXT,
            section="Results",
            text=(
                "Response increased monotonically with dose up to the mid range and "
                "then plateaued, consistent with a saturating dose-response relationship. "
                "The effect was reproducible across replicates."
            ),
        ),
        Record(
            paper_id=pid,
            source_id=f"{pid}:c3",
            modality=Modality.TEXT,
            section="Discussion",
            text=(
                "The plateau at higher doses suggests target saturation rather than "
                "toxicity, since viability of control samples was unchanged."
            ),
        ),
        Record(
            paper_id=pid,
            source_id=f"{pid}:fig3",
            modality=Modality.FIGURE,
            section="Results",
            figure_label="Figure 3",
            image_uri="demo://figure-3",
            text=(
                "Figure 3. Dose-response curve. Measured response (y-axis) versus dose "
                "(x-axis, log scale). Response rises with dose then plateaus; error bars "
                "show standard deviation across triplicates."
            ),
        ),
    ]
