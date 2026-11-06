from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database & Storage
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/patchpilot"
    redis_url: str = "redis://localhost:6379/0"
    artifact_dir: str = str(Path(__file__).resolve().parents[3] / "data" / "artifacts")
    workspace_root: str = str(Path(__file__).resolve().parents[3] / "workspaces")
    git_local_roots: str = str(Path(__file__).resolve().parents[3] / "repos")
    config_dir: str = str(Path(__file__).resolve().parents[3] / "config")

    # Security & Auth
    secret_key: str = "patchpilot-dev-insecure-secret-key-change-in-prod"
    access_token_ttl_min: int = 60
    ws_ticket_ttl_s: int = 30
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Sandbox Runner
    runner_url: str = "http://localhost:8081"
    runner_shared_secret: str = "patchpilot-runner-dev-secret"
    runner_python_image: str = "patchpilot-runner-python:latest"
    runner_scanner_image: str = "patchpilot-runner-scanner:latest"

    # LLM Settings
    default_model: str = "local-coder"
    embedding_model: str = "local-embed"
    embedding_dim: int = 768
    allow_hosted_llm: bool = False
    ollama_base_url: str = "http://localhost:11434"
    openai_compat_base_url: str = ""
    openai_compat_api_key: str = ""
    anthropic_api_key: str = ""

    # Repair & Guard Limits
    max_repair_attempts: int = 3
    guard_max_files: int = 2
    guard_max_changed_lines: int = 30

    # Logging
    log_level: str = "INFO"

    # Contract additions (spec section 2.0)
    job_token_budget: int = 200000
    push_enabled: bool = False
    log_llm_payloads: bool = True
    fake_llm_fixtures_dir: str = ""
    session_cookie_name: str = "pp_session"
    cookie_secure: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        """Browser origins allowed by CORS."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def git_local_root_list(self) -> list[Path]:
        """Absolute local repository roots from the comma-separated allowlist."""
        return [Path(r.strip()) for r in self.git_local_roots.split(",") if r.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

