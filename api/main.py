"""FastAPI entrypoint.

Run: uvicorn api.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .pipeline import answer_question
from .schemas import AskRequest, AskResponse
from .store import DemoStore, PgVectorStore, Store

app = FastAPI(
    title="PaperLens",
    version="0.1.0",
    description="Multi-modal RAG over scientific papers: cited answers over text and figures.",
)


def _build_store() -> Store:
    settings = get_settings()
    if settings.store_backend == "demo":
        return DemoStore()
    if settings.store_backend == "pgvector":
        from .embeddings import build_embedder

        embedder = build_embedder(
            settings.embedder, settings.embedding_model, settings.embedding_dim
        )
        return PgVectorStore(settings.database_url, embedder)
    raise RuntimeError(f"unknown store_backend={settings.store_backend!r}")


# One store instance for the process. Cheap for the demo; the pgvector store
# will hold a connection pool here later.
_store: Store = _build_store()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "backend": _store.name}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    return answer_question(req, _store)
