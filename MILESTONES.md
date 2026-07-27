# Milestones

Six weekly milestones. Each ends with something runnable and committed. "Ugly is fine" — the goal is a working slice every week, widening each time.

Legend: ☐ not started · ◐ in progress · ☑ done

---

## Week 1 — Skeleton + deploy something ☑
**Goal: a running API in the cloud on day one, even with a fake corpus.**
- ☑ Repo, README one-pager, milestones, license, `.gitignore`
- ☑ FastAPI app with `/health` and `/ask`
- ☑ In-memory demo store so `/ask` returns a real, cited answer shape with zero setup
- ☐ Deploy the API publicly (Fly.io / Render) — URL in README
- ☐ Dockerfile builds and runs clean

**Done when:** a stranger can `curl` the deployed `/ask` and get a structured, cited (if canned) response.

---

## Week 2 — Real corpus ingestion (text only)
**Goal: real papers in the store, text retrieval working end to end.**
- ☐ Fetch ~50 papers from the PMC Open Access subset
- ☐ Parse into sections; chunk text with overlap; keep section + paper metadata
- ☐ Embed chunks; write to pgvector; wire `docker-compose` Postgres
- ☐ Swap `/ask` from the demo store to real dense retrieval over text chunks
- ☐ Answers cite real passages (paper id + section + chunk)

**Done when:** ask a text question, get an answer grounded in real retrieved passages with working citations.

---

## Week 3 — Figures as a second modality
**Goal: figures are retrievable and feed the answer.**
- ☐ Extract figures + captions during ingestion; store image bytes/URI + caption
- ☐ Embed captions (and/or image embeddings) into a `figures` table
- ☐ Hybrid retrieval: top-k text chunks *and* top-k figures for a query, fused
- ☐ Pass retrieved figure images to the VLM (Claude vision), not just captions
- ☐ Answers can cite a specific figure by id

**Done when:** "What does Figure N show…" returns an answer that actually reasoned over the figure image and cites it.

---

## Week 4 — Grounded generation + multi-hop context assembly
**Goal: answers that span sections and refuse when unsupported.**
- ☐ Context assembler: pack text + figure context into a token budget, dedupe, order
- ☐ Prompt + structured output: answer, per-claim citations, confidence, refusal path
- ☐ Multi-hop: retrieve method (one section) + result (another) for one question
- ☐ Hard refusal when retrieval returns nothing relevant — no hallucinated answers

**Done when:** a question needing a method from §2 and a result from §4 gets one coherent, cited answer; an out-of-corpus question gets an honest "not supported."

---

## Week 5 — Evaluation + hallucination benchmark
**Goal: numbers, not vibes.**
- ☐ Held-out question set with known answers + expected source spans
- ☐ Retrieval metrics: recall@k, MRR for text and figures
- ☐ Groundedness / citation-accuracy scoring (claim → cited source supports it)
- ☐ Refusal correctness on unanswerable questions
- ☐ Results table in README; note failure modes

**Done when:** the README shows measured retrieval and groundedness numbers with a reproducible eval script.

---

## Week 6 — Frontend document viewer
**Goal: see the citations, not just read JSON.**
- ☐ Next.js app: question box + answer with inline citation chips
- ☐ Document viewer: render the source paper, highlight cited passages
- ☐ Figure panel: show cited figure with its caption alongside the answer
- ☐ Deploy the frontend; link it from the API and README

**Done when:** ask a question in the browser, read the cited answer, click a citation and see the exact passage/figure highlighted in the paper.

---

## Stretch (post-v1)
- Cross-paper synthesis ("what do these 5 papers agree/disagree on?")
- Re-ranking retrieved results with a cross-encoder
- Image embeddings (CLIP-style) in addition to caption embeddings
- Streaming answers; latency budget
