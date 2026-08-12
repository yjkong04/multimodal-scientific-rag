"""Pure, store-agnostic scoring functions.

Everything here takes plain ids / strings / citations and returns a number, so
each metric is unit-testable in isolation and reused unchanged across the demo
backend, the pgvector corpus, and every VLM in the comparison sweep.

A metric returns ``None`` when it is undefined for a case (e.g. recall with no
gold ids, precision with nothing cited). Aggregation skips ``None`` rather than
counting it as zero, so an undefined case never silently drags a mean down.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from api.schemas import Citation

# --- retrieval -------------------------------------------------------------


def recall_at_k(retrieved_ids: Sequence[str], gold_ids: Collection[str], k: int) -> float | None:
    """Fraction of gold sources present in the top-k retrieved ids.

    None when there are no gold ids (recall is undefined for an unanswerable
    case).
    """
    gold = set(gold_ids)
    if not gold:
        return None
    topk = set(retrieved_ids[:k])
    return len(gold & topk) / len(gold)


def reciprocal_rank(retrieved_ids: Sequence[str], gold_ids: Collection[str]) -> float:
    """1 / rank of the first retrieved gold source (0.0 if none retrieved)."""
    gold = set(gold_ids)
    for rank, sid in enumerate(retrieved_ids, start=1):
        if sid in gold:
            return 1.0 / rank
    return 0.0


# --- citation grounding ----------------------------------------------------


def citation_precision(cited_ids: Collection[str], gold_ids: Collection[str]) -> float | None:
    """Of the sources the answer cited, the fraction that are gold.

    None when nothing was cited (precision is undefined with an empty set).
    """
    cited = list(cited_ids)
    if not cited:
        return None
    gold = set(gold_ids)
    return sum(1 for c in cited if c in gold) / len(cited)


def citation_recall(cited_ids: Collection[str], gold_ids: Collection[str]) -> float | None:
    """Of the gold sources, the fraction the answer cited.

    None when there are no gold ids.
    """
    gold = set(gold_ids)
    if not gold:
        return None
    return len(gold & set(cited_ids)) / len(gold)


_MARKER = re.compile(r"\[([^\[\]]+)\]")


def inline_markers(answer: str) -> list[str]:
    """Bracketed inline citations in an answer, e.g. '[Figure 3]' -> 'Figure 3'."""
    return [m.strip() for m in _MARKER.findall(answer)]


def _marker_labels(citations: Iterable[Citation]) -> set[str]:
    labels: set[str] = set()
    for c in citations:
        if c.figure_label:
            labels.add(c.figure_label.lower())
        if c.section:
            labels.add(c.section.lower())
    return labels


def _marker_supported(marker: str, labels: set[str]) -> bool:
    m = marker.lower().strip()
    return any(m == lab or lab in m or m in lab for lab in labels)


def groundedness(answer: str, citations: Sequence[Citation]) -> float | None:
    """Fraction of the answer's inline citation markers that name a real source.

    Measures whether the model cites *what it was given*: every '[Methods]' /
    '[Figure 3]' marker must match a section or figure label present in the
    citations. None when the answer carries no markers (undefined), which is the
    case for the marker-free extractive baseline — it is scored by citation
    precision/recall instead.
    """
    markers = inline_markers(answer)
    if not markers:
        return None
    labels = _marker_labels(citations)
    supported = sum(1 for m in markers if _marker_supported(m, labels))
    return supported / len(markers)


# --- refusal ---------------------------------------------------------------


@dataclass
class RefusalTally:
    """Confusion counts for the answer/refuse decision, over a set of cases.

    Feed it (answerable, status) pairs; read precision/recall/accuracy off it.
    """

    answered_when_answerable: int = 0  # correct answer
    refused_when_answerable: int = 0  # over-refusal (missed a real answer)
    refused_when_unanswerable: int = 0  # correct refusal
    answered_when_unanswerable: int = 0  # hallucination risk

    def add(self, *, answerable: bool, status: str) -> None:
        answered = status == "answered"
        if answerable and answered:
            self.answered_when_answerable += 1
        elif answerable and not answered:
            self.refused_when_answerable += 1
        elif not answerable and not answered:
            self.refused_when_unanswerable += 1
        else:
            self.answered_when_unanswerable += 1

    @property
    def total(self) -> int:
        return (
            self.answered_when_answerable
            + self.refused_when_answerable
            + self.refused_when_unanswerable
            + self.answered_when_unanswerable
        )

    @property
    def answer_accuracy(self) -> float | None:
        """Fraction of cases where the answer/refuse decision was correct."""
        if self.total == 0:
            return None
        correct = self.answered_when_answerable + self.refused_when_unanswerable
        return correct / self.total

    @property
    def refusal_recall(self) -> float | None:
        """Of the unanswerable cases, the fraction correctly refused."""
        unanswerable = self.refused_when_unanswerable + self.answered_when_unanswerable
        if unanswerable == 0:
            return None
        return self.refused_when_unanswerable / unanswerable

    @property
    def refusal_precision(self) -> float | None:
        """Of the cases refused, the fraction that were truly unanswerable."""
        refused = self.refused_when_unanswerable + self.refused_when_answerable
        if refused == 0:
            return None
        return self.refused_when_unanswerable / refused


def mean(values: Iterable[float | None]) -> float | None:
    """Mean over the defined (non-None) values; None if none are defined."""
    defined = [v for v in values if v is not None]
    if not defined:
        return None
    return sum(defined) / len(defined)
