# PaperLens v2 — Design Doc

**Paste one or more PDFs the system has never seen, ask questions, and get grounded, cited answers — with background context pulled in for the concepts the paper assumes you already know.**

v1 answered questions over a fixed, pre-ingested corpus (PMC Open Access, clean JATS XML). v2 removes both limits: the papers are arbitrary user PDFs supplied at query time, and the answer is enriched with background from trusted sources so a reader who lacks the paper's assumed context still gets a reliable answer.

---

## Locked decisions (these shape everything below)

1. **A trained component is a means, not a goal.** Use pretrained models wherever they do the job (PDF parsing, embeddings, figure reasoning, generation). Train/fine-tune something *only* when it's the actual bottleneck — never to have "trained a model" on the résumé. No training infrastructure for show.
2. **Enrichment starts small and widens over epochs.** Ground first from the existing PMC corpus only; add curated textbooks next; add open web search last, each behind reliability guardrails. Never open a broader (riskier) source before the narrower one is solid.
3. **Pasted PDFs are ephemeral, per session.** They are parsed into a session-scoped index, used to answer, and discarded when the session ends. They never pollute the persistent corpus.
4. **No per-paper training.** A new paper flows through *retrieval*, not through *training*. Models are trained once, offline, and reused.

---

## Why not "a CNN that trains itself on each new paper"

Per-paper training is the wrong tool: you can't meaningfully train a network on one document, it's slow and unstable, and it would degrade the model for every other paper. The capability — answer over an unseen PDF — is a **dynamic retrieval** problem. The paper gets *ingested into an index at query time*, not learned by a model. This is both more reliable and far cheaper.

Where ML genuinely lives in v2:

| Component | Model | Trained? |
|---|---|---|
| PDF layout / structure parsing | Nougat (academic-PDF OCR→markdown), GROBID (structure + refs), PyMuPDF fallback | Pretrained. Fine-tune a figure/table detector *only* if parse quality blocks us. |
| Retrieval embeddings | `sentence-transformers` (e.g. SPECTER2 / BGE) | Pretrained. Fine-tune on the PMC corpus *only* if retrieval quality blocks us. |
| Figure reasoning + answer generation | Claude (vision) | Pretrained, used as-is. |
| Concept extraction | LLM / lightweight NER | Pretrained. |

The one honest place "learn from open-access papers" could apply is an *offline* embedder fine-tune on the accumulated corpus — done once, on the corpus, not per paper. Deferred until retrieval quality demands it (decision #1).

---

## The hard part: arbitrary PDFs have no JATS XML

v1 had it easy — PMC handed us tagged sections, captions, and figures. A user's PDF is a wall of positioned glyphs. Recovering structure (sections, columns, tables, figures + captions) from raw PDF is the central new engineering problem, and it's where a vision model earns its place. Pipeline: try Nougat for a structured markdown pass, GROBID for section/reference structure, PyMuPDF for text + embedded images as a floor, and reconcile.

---

## The differentiated part: context enrichment (done safely)

Pulling background so a paper's assumed concepts are explained is the feature few have built — and it's where reliability dies if it's careless. Structure:

- **Concept extraction:** identify the key terms, methods, and assumed background in the pasted paper.
- **Tiered sources, most-trusted first** (widened over epochs per decision #2):
  1. Existing PMC corpus (fully grounded, already ours) — **v2 ships with this only.**
  2. Curated textbooks (licensed / open) — added once tier 1 is solid.
  3. Open web search — added last, behind source-quality filtering.
- **Provenance separation is non-negotiable.** Every answer visibly distinguishes *"from your pasted paper"* vs *"background context from source X."* Blurring them destroys the grounding guarantee that is the whole point. Citations carry their tier.
- **Refuse over guess.** If neither the paper nor acceptable enrichment supports a claim, say so — the v1 refusal contract, extended to enrichment.

---

## Architecture (v2)

```
  user pastes PDF(s)
        ▼
  ┌───────────────────────────┐
  │ Parse: Nougat/GROBID/     │  arbitrary PDF -> sections + figures
  │ PyMuPDF, reconciled       │
  └────────────┬──────────────┘
               ▼
  ┌───────────────────────────┐
  │ Ephemeral SESSION index   │  chunk + embed, scoped to this session, TTL
  │ (in-memory / pgvector ns) │
  └────────────┬──────────────┘
               ▼
  question ─► Concept extraction ─► Tiered enrichment retrieval
               │                       (corpus -> textbooks -> web)
               ▼                       │
  Hybrid retrieval over session index ─┘
               ▼
  Grounded generation (Claude), provenance-separated citations
               ▼
  Frontend: answer with "your paper" vs "background" citations,
            highlighted in the document viewer
               ▼
  session ends ─► ephemeral index discarded
```

Reuses v1 wholesale: the chunk → embed → retrieve → cite → refuse pipeline is identical; v2 adds (a) a real PDF parser, (b) a session-scoped ephemeral index, and (c) tiered, provenance-separated enrichment.

---

## Milestones (6 weeks, each ends runnable)

### Week 1 — Arbitrary PDF ingestion
Parse a pasted PDF (no JATS) into sections + figures via Nougat/GROBID/PyMuPDF, reconciled. Build the ephemeral session store. **Done when:** upload a PDF, get structured chunks + extracted figures back.

### Week 2 — Session-scoped answers
`/ask` over the pasted PDF(s), ephemerally, reusing v1's retrieve→cite→generate. **Done when:** paste a PDF, ask a question, get an answer citing that paper; session teardown discards the index.

### Week 3 — Enrichment tier 1 (existing corpus)
Concept extraction + background retrieval from the PMC corpus, included as separately-cited context with provenance tags. **Done when:** an answer visibly separates "your paper" from "background (corpus)."

### Week 4 — Enrichment tier 2 (curated textbooks)
Add a curated, licensed/open textbook source behind the same provenance + quality structure. **Done when:** background can come from textbooks, clearly labeled, without degrading grounding.

### Week 5 — Enrichment tier 3 (web) + reliability
Add open web search behind source-quality filtering; extend the hallucination benchmark to enriched answers; refuse when enrichment is weak. **Done when:** measured groundedness holds with web enrichment on, and low-quality sources are filtered or refused.

### Week 6 — Frontend
Paste/upload PDFs, ask, read answers with provenance-separated citations (paper vs background), highlighted in the viewer. **Done when:** the full flow works in the browser end to end.

### Optional, only if a bottleneck (decision #1)
Fine-tune the embedder on the corpus (retrieval quality) or a figure/table detector (parse quality). Not on the critical path.

---

## Open questions for later
- Session index substrate: pure in-memory vs a TTL'd pgvector namespace (matters once PDFs are large or many).
- Textbook source: which corpus, and its license.
- Web-source trust: allowlist domains, or score-and-filter?
