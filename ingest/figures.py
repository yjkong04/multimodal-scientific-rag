"""Resolve the public URL of a PMC figure image.

The JATS `<graphic>` href is a bare filename; PMC serves the rendered image for
that figure at a canonical per-article `/bin/` path. We store that URL in
`figures.image_uri` rather than downloading and rehosting the bytes:

- the document viewer links to it directly, and
- the vision step fetches it on demand at inference time.

This keeps ingestion cheap and avoids duplicating NCBI's image storage. (The OA
bulk `.tar.gz` packages are FTP-only, so downloading bytes is deliberately not
the ingestion path.)
"""

from __future__ import annotations

_PMC_ARTICLE = "https://pmc.ncbi.nlm.nih.gov/articles"


def figure_image_url(pmcid: str, graphic_href: str) -> str:
    """Canonical URL of a figure image, e.g.
    https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/bin/fig1.jpg
    """
    return f"{_PMC_ARTICLE}/{pmcid}/bin/{graphic_href}"
