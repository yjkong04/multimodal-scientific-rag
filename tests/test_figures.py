"""Figure image URL tests. Pure/offline."""

from ingest.chunk import chunk_paper
from ingest.figures import figure_image_url
from ingest.pmc import Figure, ParsedPaper


def test_figure_image_url_shape():
    url = figure_image_url("PMC12345", "fig1.jpg")
    assert url == "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/bin/fig1.jpg"


def test_chunk_sets_image_uri_when_graphic_present():
    paper = ParsedPaper(
        paper_id="PMC12345",
        title="t",
        sections=[],
        figures=[Figure(label="Figure 1", caption="a curve", graphic_href="g001.jpg")],
    )
    fig_chunks = [c for c in chunk_paper(paper) if c.modality == "figure"]
    assert len(fig_chunks) == 1
    assert fig_chunks[0].image_uri == "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/bin/g001.jpg"


def test_chunk_image_uri_none_without_graphic():
    paper = ParsedPaper(
        paper_id="PMC12345",
        title="t",
        sections=[],
        figures=[Figure(label="Figure 1", caption="a curve", graphic_href=None)],
    )
    fig_chunks = [c for c in chunk_paper(paper) if c.modality == "figure"]
    assert fig_chunks[0].image_uri is None
