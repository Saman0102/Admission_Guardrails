"""Runtime settings loaded from environment variables and an optional .env file."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


def model_provider() -> str:
    """Return the configured provider name."""
    return os.getenv("ADMISSIONS_MODEL", "mock").strip().lower()


def gemini_api_key() -> str:
    """Return the configured Gemini API key, if any."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def gemini_model() -> str:
    """Return the configured Gemini model name."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()


def decision_log_path(project_root: Path = PROJECT_ROOT) -> Path:
    """Resolve the decision-log path relative to the project root."""
    configured = os.getenv("ADMISSIONS_LOG_PATH", "results/decision_log.jsonl")
    path = Path(configured)
    return path if path.is_absolute() else project_root / path
