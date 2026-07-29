"""Runtime configuration, loaded from environment / .env.

Week 1 runs entirely off the in-memory demo store, so nothing here is
required. The database and model fields are placeholders the later
milestones wire up (Week 2: pgvector; Week 3: Claude vision).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PAPERLENS_", extra="ignore")

    # "demo" (in-memory, no deps) or "pgvector" (real corpus).
    store_backend: str = "demo"

    database_url: str = "postgresql://paperlens:paperlens@localhost:5432/paperlens"

    # Embeddings. "sentence-transformer" (local HF, production) or "hashing"
    # (deterministic, dependency-light, for tests/CI). Keep embedding_dim in sync
    # with the model AND db/schema.sql.
    embedder: str = "sentence-transformer"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    anthropic_api_key: str | None = None
    generation_model: str = "claude-sonnet-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
