"""Chunk parsed papers into retrieval units.

Text chunks respect section boundaries (a chunk never spans two sections, so a
citation resolves cleanly to one section) and carry a character overlap so a
fact split across a boundary is still recoverable. Figures become their own
chunks keyed off the caption.
"""

from __future__ import annotations

from dataclasses import dataclass

from .pmc import ParsedPaper


@dataclass
class Chunk:
    chunk_id: str
    paper_id: str
    modality: str  # "text" or "figure"
    section: str | None
    content: str
    figure_label: str | None = None
    fig_id: str | None = None
    ord: int = 0


def _split_with_overlap(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # Prefer to break on a sentence/space boundary near the limit.
        if end < n:
            window = text.rfind(" ", start + max_chars - overlap, end)
            if window != -1 and window > start:
                end = window
        out.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in out if c]


def chunk_paper(paper: ParsedPaper, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    chunks: list[Chunk] = []
    ordinal = 0

    for section in paper.sections:
        for piece in _split_with_overlap(section.text, max_chars, overlap):
            chunks.append(
                Chunk(
                    chunk_id=f"{paper.paper_id}:c{ordinal}",
                    paper_id=paper.paper_id,
                    modality="text",
                    section=section.title,
                    content=piece,
                    ord=ordinal,
                )
            )
            ordinal += 1

    for i, fig in enumerate(paper.figures):
        chunks.append(
            Chunk(
                chunk_id=f"{paper.paper_id}:fig{i}",
                paper_id=paper.paper_id,
                modality="figure",
                section=None,
                content=fig.caption,
                figure_label=fig.label,
                fig_id=fig.fig_id,
                ord=ordinal,
            )
        )
        ordinal += 1

    return chunks
