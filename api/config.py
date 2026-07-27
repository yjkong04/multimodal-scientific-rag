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

    # "demo" (in-memory, no deps) or "pgvector" (real corpus). Week 2 flips this.
    store_backend: str = "demo"

    # Filled in from Week 2 onward.
    database_url: str | None = None
    anthropic_api_key: str | None = None
    embedding_model: str = "text-embedding-placeholder"
    generation_model: str = "claude-sonnet-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
