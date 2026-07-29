"""Turn a question into a grounded, cited answer.

Week 1: hybrid retrieval over the demo store, then a deterministic extractive
"answer" assembled from the retrieved sources. This is a placeholder for the
VLM generation step (Week 3-4) but it already enforces the core contract:
no citations -> refuse. That refusal path is the whole point of the system,
so it is real from day one, not stubbed.
"""

from __future__ import annotations

from .schemas import AskRequest, AskResponse, Citation, Modality
from .store import ScoredRecord, Store


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


def _compose_answer(question: str, citations: list[Citation]) -> str:
    """Extractive placeholder for VLM generation.

    Stitches the top text passage and figure caption into a short answer that
    stays strictly grounded in retrieved sources. Replaced by Claude vision in
    Week 3-4; the citation list it draws from does not change.
    """
    text_bits = [c.snippet for c in citations if c.modality == Modality.TEXT]
    fig_bits = [(c.figure_label, c.snippet) for c in citations if c.modality == Modality.FIGURE]

    parts: list[str] = []
    if text_bits:
        parts.append(text_bits[0])
    if fig_bits:
        label, cap = fig_bits[0]
        parts.append(f"{label or 'The figure'} supports this: {cap}")
    return " ".join(parts)


def answer_question(req: AskRequest, store: Store) -> AskResponse:
    text_hits = store.search_text(req.question, req.top_k_text)
    figure_hits = store.search_figures(req.question, req.top_k_figures)

    citations = [_to_citation(s) for s in (*text_hits, *figure_hits)]
    citations.sort(key=lambda c: c.score, reverse=True)

    if not citations:
        return AskResponse(
            answer=(
                "I couldn't find anything in the corpus that supports an answer to "
                "that question, so I won't guess."
            ),
            citations=[],
            status="refused",
            backend=store.name,
        )

    return AskResponse(
        answer=_compose_answer(req.question, citations),
        citations=citations,
        status="answered",
        backend=store.name,
    )
