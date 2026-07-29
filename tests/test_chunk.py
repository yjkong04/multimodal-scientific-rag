"""Chunker tests. Pure functions, no network — these run anywhere."""

from ingest.chunk import chunk_paper
from ingest.pmc import Figure, ParsedPaper, Section


def _paper() -> ParsedPaper:
    return ParsedPaper(
        paper_id="PMC0001",
        title="A test paper",
        sections=[
            Section(title="Methods", text="word " * 500),  # long -> multiple chunks
            Section(title="Results", text="Response rose with dose then plateaued."),
        ],
        figures=[Figure(label="Figure 1", caption="Dose-response curve.", fig_id="f1")],
    )


def test_chunks_cover_text_and_figures():
    chunks = chunk_paper(_paper(), max_chars=400, overlap=50)
    text = [c for c in chunks if c.modality == "text"]
    figs = [c for c in chunks if c.modality == "figure"]
    assert len(text) >= 3, "the long Methods section should split into several chunks"
    assert len(figs) == 1
    assert figs[0].figure_label == "Figure 1"


def test_chunk_ids_unique_and_carry_section():
    chunks = chunk_paper(_paper(), max_chars=400, overlap=50)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk ids must be unique"
    methods = [c for c in chunks if c.section == "Methods"]
    assert methods and all(c.paper_id == "PMC0001" for c in methods)


def test_chunks_never_span_sections():
    chunks = chunk_paper(_paper(), max_chars=400, overlap=50)
    # Every text chunk belongs to exactly one known section.
    sections = {c.section for c in chunks if c.modality == "text"}
    assert sections == {"Methods", "Results"}
