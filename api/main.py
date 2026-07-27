"""FastAPI entrypoint.

Run: uvicorn api.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .pipeline import answer_question
from .schemas import AskRequest, AskResponse
from .store import DemoStore, Store

app = FastAPI(
    title="PaperLens",
    version="0.1.0",
    description="Multi-modal RAG over scientific papers: cited answers over text and figures.",
)


def _build_store() -> Store:
    settings = get_settings()
    # Week 2 adds: if settings.store_backend == "pgvector": return PgVectorStore(...)
    if settings.store_backend != "demo":
        raise RuntimeError(
            f"store_backend={settings.store_backend!r} is not wired up yet; use 'demo'"
        )
    return DemoStore()


# One store instance for the process. Cheap for the demo; the pgvector store
# will hold a connection pool here later.
_store: Store = _build_store()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "backend": _store.name}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    return answer_question(req, _store)
