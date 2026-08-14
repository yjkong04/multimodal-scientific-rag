"""Run the eval set through the real pipeline and score every case.

`evaluate()` is the one entry point: give it a `Store`, a `Generator`, and a
list of `EvalCase`, and it returns an `EvalReport` holding per-case rows and
aggregate metrics. It scores two things per case:

- retrieval, from the raw store hits (generator-independent), and
- generation + refusal, from the real `answer_question` pipeline, so the numbers
  reflect the assembler and relevance gate, not just the retriever.

The report is a plain dataclass, so `report.py` can render it and the sweep can
collect many of them without any of the scoring logic knowing how it's shown.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from api.generation import Generator
from api.pipeline import answer_question
from api.schemas import AskRequest
from api.store import Store

from . import metrics
from .dataset import EvalCase


@dataclass
class CaseResult:
    case: EvalCase
    status: str  # "answered" | "refused"
    retrieved_ids: list[str]  # ranked union of text+figure hits
    cited_ids: list[str]  # sources the answer actually cited
    recall_at_k: float | None
    reciprocal_rank: float
    citation_precision: float | None
    citation_recall: float | None
    groundedness: float | None


@dataclass
class EvalReport:
    backend: str
    generator: str
    k: int
    results: list[CaseResult] = field(default_factory=list)

    # --- aggregate metrics (means over the cases where each is defined) ---

    @property
    def recall_at_k(self) -> float | None:
        return metrics.mean(r.recall_at_k for r in self.results)

    @property
    def mrr(self) -> float | None:
        # MRR is over answerable cases only; unanswerable cases have no gold rank.
        return metrics.mean(
            r.reciprocal_rank for r in self.results if r.case.answerable
        )

    @property
    def citation_precision(self) -> float | None:
        return metrics.mean(r.citation_precision for r in self.results)

    @property
    def citation_recall(self) -> float | None:
        return metrics.mean(r.citation_recall for r in self.results)

    @property
    def groundedness(self) -> float | None:
        return metrics.mean(r.groundedness for r in self.results)

    @property
    def refusal(self) -> metrics.RefusalTally:
        tally = metrics.RefusalTally()
        for r in self.results:
            tally.add(answerable=r.case.answerable, status=r.status)
        return tally


def _ranked_retrieved_ids(store: Store, question: str, k_text: int, k_figures: int) -> list[str]:
    """Merge the text and figure hits into one score-ranked id list."""
    hits = [*store.search_text(question, k_text), *store.search_figures(question, k_figures)]
    hits.sort(key=lambda s: s.score, reverse=True)
    return [s.record.source_id for s in hits]


def evaluate(
    store: Store,
    generator: Generator,
    cases: list[EvalCase],
    *,
    k_text: int = 4,
    k_figures: int = 2,
) -> EvalReport:
    k = k_text + k_figures
    report = EvalReport(backend=store.name, generator=type(generator).__name__, k=k)

    for case in cases:
        retrieved = _ranked_retrieved_ids(store, case.question, k_text, k_figures)
        req = AskRequest(question=case.question, top_k_text=k_text, top_k_figures=k_figures)
        resp = answer_question(req, store, generator)
        cited = [c.source_id for c in resp.citations]

        # Citation/groundedness metrics only make sense for cases that *should*
        # be answered; on unanswerable cases the right behavior is to cite
        # nothing, which the refusal tally captures instead.
        report.results.append(
            CaseResult(
                case=case,
                status=resp.status,
                retrieved_ids=retrieved,
                cited_ids=cited,
                recall_at_k=metrics.recall_at_k(retrieved, case.gold_source_ids, k),
                reciprocal_rank=metrics.reciprocal_rank(retrieved, case.gold_source_ids),
                citation_precision=(
                    metrics.citation_precision(cited, case.gold_source_ids)
                    if case.answerable
                    else None
                ),
                citation_recall=(
                    metrics.citation_recall(cited, case.gold_source_ids)
                    if case.answerable
                    else None
                ),
                groundedness=(
                    metrics.groundedness(resp.answer, resp.citations)
                    if case.answerable
                    else None
                ),
            )
        )

    return report
