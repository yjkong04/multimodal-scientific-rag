# PaperLens

[![repo](https://img.shields.io/badge/github-yjkong04%2Fpaperlens-blue)](https://github.com/yjkong04/paperlens)

**A multi-modal RAG system that answers questions by reasoning over both the text and the figures in scientific papers — and cites exactly where each part of the answer came from.**

Ask *"What does Figure 3 show about the relationship between drug dose and tumor volume?"* and get a grounded, cited answer that pulls from the figure, its caption, and the surrounding methods and results — not a hallucination.

---

## The one-pager

### Problem
Text-only RAG is table stakes. But scientific knowledge lives as much in figures, plots, and diagrams as in prose — and the two are inseparable: a result in Figure 3 only makes sense next to the method in Section 2. Standard RAG throws the figures away and answers from text alone, so it either can't answer figure questions or makes something up. Answering them well means retrieving across *two modalities* and assembling context that spans both.

### User
- **Primary:** a researcher, grad student, or analyst doing a literature review who needs to interrogate a corpus of papers fast and trust the answer enough to cite it.
- **Corpus:** the [PubMed Central Open Access subset](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/) — life-sciences papers with figures, clean licensing, real biomedical content.
- **Trust requirement:** every claim in an answer links back to a specific passage or figure. No citation, no claim.

### What "done" looks like (v1)
1. Ingest ~200 open-access papers: text chunked, figures extracted with captions, both embedded and stored.
2. A question hits **hybrid retrieval** over text chunks *and* figure records, and the top-k from both modalities are assembled into one context window.
3. A vision-language model (Claude) generates an answer that **cites specific figures and passages** and refuses when the corpus doesn't support an answer.
4. A **document viewer** frontend renders the source paper with the cited passages and figures highlighted.
5. A **hallucination benchmark**: a held-out question set with known answers, scored for groundedness, citation accuracy, and refusal-when-unsupported.

### Explicitly out of scope for v1
Multi-paper synthesis across the whole corpus, PDF layout parsing beyond what the tooling gives us, user accounts, and fine-tuning any model. Retrieval + grounded generation + citation is the whole job for v1.

### What I'd need to learn
- **Vision-language model integration** — passing figures (not just captions) to a VLM and getting grounded, structured output back.
- **Multi-vector / hybrid retrieval** — combining dense text embeddings with figure/caption embeddings and fusing the rankings sensibly.
- **Context assembly across modalities** — packing text + image context into a budget so the answer can span sections (multi-hop).
- **Retrieval + hallucination evaluation** — building a benchmark that actually measures grounding, not just "looks plausible."
- **pgvector at a real (small) scale** — indexing, distance operators, and query performance.

---

## Architecture (v1)

```
                 ┌──────────────────────────────────────────┐
   PMC OA  ──►   │  Ingestion:  text chunks + figures        │
   papers        │  (caption, image bytes) → embeddings      │
                 └───────────────┬──────────────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │  pgvector store │  text_chunks · figures
                        └────────┬────────┘
                                 ▼
   question ─►  Hybrid retrieval (text k + figures k)  ─►  Context assembly
                                 │                              │
                                 ▼                              ▼
                        VLM (Claude) generates grounded, cited answer
                                 │
                                 ▼
                Next.js viewer: paper with highlighted citations
```

## Stack
- **Backend:** Python, FastAPI
- **Vector store:** Postgres + pgvector
- **VLM:** Claude (vision) for figure reasoning and answer generation; embeddings for retrieval
- **Frontend:** Next.js document viewer (later milestone)

## Status
Early. See [MILESTONES.md](./MILESTONES.md) for the plan and current milestone. The API runs today — see below.

## Quickstart

```bash
# 1. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the API (works with the built-in demo store, no DB required)
uvicorn api.main:app --reload

# 3. Try it
curl -s localhost:8000/health
curl -s -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "What does the figure show about dose and response?"}' | python3 -m json.tool
```

For the full pipeline with Postgres/pgvector, see [`docker-compose.yml`](./docker-compose.yml) and `.env.example`.

## License
MIT
