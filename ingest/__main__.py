"""Ingestion CLI: fetch open-access PMC papers and chunk them.

    # Dry run: fetch, parse, chunk, print a summary
    python -m ingest --query "CRISPR gene editing" --limit 5

    # Embed and write into pgvector (needs a running DB; see docker-compose.yml)
    python -m ingest --pmcids PMC13403225 PMC13402739 --write
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
    parser.add_argument("--write", action="store_true", help="embed and write into pgvector")
    args = parser.parse_args()

    enable_os_trust_store()

    conn = writer = embedder = None
    if args.write:
        import psycopg

        from api.config import get_settings
        from api.embeddings import build_embedder
        from .index import write_paper

        settings = get_settings()
        embedder = build_embedder(settings.embedder, settings.embedding_model, settings.embedding_dim)
        conn = psycopg.connect(settings.database_url, autocommit=True)
        writer = write_paper

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
        if args.write:
            tc, fc = writer(conn, paper, chunks, embedder)
        else:
            tc = sum(1 for c in chunks if c.modality == "text")
            fc = sum(1 for c in chunks if c.modality == "figure")
        total_text += tc
        total_fig += fc
        title = (paper.title or "(untitled)")[:70]
        wrote = " (written)" if args.write else ""
        print(f"  {pmcid}: {tc} text + {fc} figure chunks{wrote} | {title}")

    dest = " into pgvector" if args.write else ""
    print(f"total: {total_text} text chunks, {total_fig} figure chunks across {len(pmcids)} papers{dest}")

    if conn is not None:
        conn.close()


if __name__ == "__main__":
    main()
