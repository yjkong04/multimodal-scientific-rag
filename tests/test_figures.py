"""Figure parsing tests. Pure/offline — build JATS snippets in-memory, no network."""

from xml.etree import ElementTree as ET

from ingest.chunk import chunk_paper
from ingest.pmc import Figure, ParsedPaper, _graphic_href, parse_article

XLINK = 'xmlns:xlink="http://www.w3.org/1999/xlink"'


def _fig(xml: str) -> ET.Element:
    return ET.fromstring(xml)


def test_graphic_href_xlink_namespaced():
    fig = _fig(f'<fig {XLINK}><label>Figure 1</label><graphic xlink:href="f1.jpg"/></fig>')
    assert _graphic_href(fig) == "f1.jpg"


def test_graphic_href_bare_href():
    fig = _fig('<fig><graphic href="f1.jpg"/></fig>')
    assert _graphic_href(fig) == "f1.jpg"


def test_graphic_href_ignores_inline_graphic_in_caption():
    # An <inline-graphic> in the caption precedes the real <graphic>; must be skipped.
    fig = _fig(
        f'<fig {XLINK}><caption><p>see <inline-graphic xlink:href="icon.gif"/></p></caption>'
        f'<graphic xlink:href="real.jpg"/></fig>'
    )
    assert _graphic_href(fig) == "real.jpg"


def test_graphic_href_prefers_direct_child_over_nested():
    fig = _fig(
        f'<fig {XLINK}><caption><graphic xlink:href="caption.jpg"/></caption>'
        f'<graphic xlink:href="main.jpg"/></fig>'
    )
    assert _graphic_href(fig) == "main.jpg"


def test_graphic_href_none_when_absent():
    fig = _fig('<fig><label>Figure 1</label></fig>')
    assert _graphic_href(fig) is None


def test_parse_article_keeps_caption_less_figure_with_image():
    xml = (
        f'<article {XLINK}><front><article-meta><title-group>'
        f"<article-title>T</article-title></title-group></article-meta></front>"
        f"<body><sec><title>S</title><p>body text</p>"
        f'<fig><label>Figure 1</label><graphic xlink:href="f1.jpg"/></fig>'
        f"</sec></body></article>"
    )
    paper = parse_article(xml.encode(), "PMC1")
    assert len(paper.figures) == 1
    assert paper.figures[0].caption == ""  # no caption, but retained
    assert paper.figures[0].graphic_href == "f1.jpg"


def test_parse_article_drops_figure_with_neither_caption_nor_image():
    xml = (
        f"<article {XLINK}><body><sec><title>S</title><p>t</p>"
        f"<fig><label>Figure 1</label></fig></sec></body></article>"
    )
    paper = parse_article(xml.encode(), "PMC1")
    assert paper.figures == []


def test_chunk_copies_image_uri_and_falls_back_to_label():
    paper = ParsedPaper(
        paper_id="PMC1",
        title="t",
        sections=[],
        figures=[Figure(label="Figure 1", caption="", graphic_href="f1.jpg", image_uri="https://cdn/f1.jpg")],
    )
    figc = [c for c in chunk_paper(paper) if c.modality == "figure"]
    assert len(figc) == 1
    assert figc[0].image_uri == "https://cdn/f1.jpg"
    assert figc[0].content == "Figure 1"  # caption-less -> label fallback so it's retrievable
