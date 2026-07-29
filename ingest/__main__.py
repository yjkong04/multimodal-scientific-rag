"""Ingestion CLI: fetch open-access PMC papers and chunk them.

    python -m ingest --query "CRISPR gene editing" --limit 5
    python -m ingest --pmcids PMC13403225 PMC13402739

For now this prints a summary of what was parsed and chunked. Wiring the chunks
into pgvector with embeddings is the next step in Week 2.
"""

from __future__ import annotations

import argparse

from .chunk import chunk_paper
from .net import enable_os_trust_store
from .pmc import fetch_and_parse, search_oa_pmcids


def main() -> None:
    parser = argparse.ArgumentParser(prog="ingest", description=__doc__)
    parser.add_argument("--query", help="search the PMC open-access subset")
    parser.add_argument("--pmcids", nargs="+", help="explicit PMCIDs to fetch")
    parser.add_argument("--limit", type=int, default=5, help="max papers for --query")
    args = parser.parse_args()

    enable_os_trust_store()

    if args.pmcids:
        pmcids = args.pmcids
    elif args.query:
        pmcids = search_oa_pmcids(args.query, limit=args.limit)
        print(f"query {args.query!r} -> {len(pmcids)} open-access papers")
    else:
        parser.error("provide --query or --pmcids")

    total_text = total_fig = 0
    for pmcid in pmcids:
        paper = fetch_and_parse(pmcid)
        chunks = chunk_paper(paper)
        tc = sum(1 for c in chunks if c.modality == "text")
        fc = sum(1 for c in chunks if c.modality == "figure")
        total_text += tc
        total_fig += fc
        title = (paper.title or "(untitled)")[:70]
        print(f"  {pmcid}: {tc} text + {fc} figure chunks | {title}")

    print(f"total: {total_text} text chunks, {total_fig} figure chunks across {len(pmcids)} papers")


if __name__ == "__main__":
    main()
