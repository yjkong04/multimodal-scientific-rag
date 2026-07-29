"""Turn a question into a grounded, cited answer.

Week 1: hybrid retrieval over the demo store, then a deterministic extractive
"answer" assembled from the retrieved sources. This is a placeholder for the
VLM generation step (Week 3-4) but it already enforces the core contract:
no citations -> refuse. That refusal path is the whole point of the system,
so it is real from day one, not stubbed.
"""

from __future__ import annotations

from .generation import Generator
from .schemas import AskRequest, AskResponse, Citation
from .store import ScoredRecord, Store

_REFUSAL = (
    "I couldn't find anything in the corpus that supports an answer to that "
    "question, so I won't guess."
)


def _to_citation(scored: ScoredRecord) -> Citation:
    r = scored.record
    return Citation(
        modality=r.modality,
        paper_id=r.paper_id,
        source_id=r.source_id,
        section=r.section,
        figure_label=r.figure_label,
        image_uri=r.image_uri,
        snippet=r.text,
        score=round(scored.score, 4),
    )


def answer_question(req: AskRequest, store: Store, generator: Generator) -> AskResponse:
    text_hits = store.search_text(req.question, req.top_k_text)
    figure_hits = store.search_figures(req.question, req.top_k_figures)

    citations = [_to_citation(s) for s in (*text_hits, *figure_hits)]
    citations.sort(key=lambda c: c.score, reverse=True)

    # Nothing retrieved, or the generator couldn't ground an answer -> refuse.
    answer = generator.generate(req.question, citations) if citations else ""
    if not answer.strip():
        return AskResponse(answer=_REFUSAL, citations=[], status="refused", backend=store.name)

    return AskResponse(
        answer=answer, citations=citations, status="answered", backend=store.name
    )
