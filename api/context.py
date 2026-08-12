"""Assemble retrieved citations into the context the generator sees.

Top-k retrieval alone tends to return several near-duplicate chunks from the
same section, which crowds out the complementary evidence a multi-hop question
needs (a method in one section, a result in another). The assembler:

1. dedupes by source,
2. caps chunks per section so the context spans sections (multi-hop coverage),
3. fits a character budget, dropping the weakest chunks first,
4. always keeps a few top figures (the multimodal signal).

It operates on a larger candidate pool than the final context so there is
something to diversify down to. Returned citations are exactly what grounded the
answer, in score order.
"""

from __future__ import annotations

from .schemas import Citation, Modality


def assemble_context(
    citations: list[Citation],
    *,
    char_budget: int = 4000,
    per_section_cap: int = 2,
    max_figures: int = 3,
) -> list[Citation]:
    text = sorted(
        (c for c in citations if c.modality == Modality.TEXT),
        key=lambda c: c.score,
        reverse=True,
    )
    figures = sorted(
        (c for c in citations if c.modality == Modality.FIGURE),
        key=lambda c: c.score,
        reverse=True,
    )

    chosen_text: list[Citation] = []
    seen_ids: set[str] = set()
    per_section: dict[tuple[str, str | None], int] = {}
    used = 0
    for c in text:
        if c.source_id in seen_ids:  # dedupe exact chunks
            continue
        key = (c.paper_id, c.section)
        if per_section.get(key, 0) >= per_section_cap:  # section diversity
            continue
        if chosen_text and used + len(c.snippet) > char_budget:  # budget (keep >=1)
            break
        seen_ids.add(c.source_id)
        per_section[key] = per_section.get(key, 0) + 1
        used += len(c.snippet)
        chosen_text.append(c)

    chosen_figs: list[Citation] = []
    seen_figs: set[str] = set()
    for c in figures:
        if c.source_id in seen_figs:
            continue
        seen_figs.add(c.source_id)
        chosen_figs.append(c)
        if len(chosen_figs) >= max_figures:
            break

    combined = chosen_text + chosen_figs
    combined.sort(key=lambda c: c.score, reverse=True)
    return combined


def sections_covered(citations: list[Citation]) -> int:
    """Number of distinct (paper, section) text sources — a multi-hop coverage proxy."""
    return len({(c.paper_id, c.section) for c in citations if c.modality == Modality.TEXT})
