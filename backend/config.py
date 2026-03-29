from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

DB_PATH = BACKEND_ROOT / "pulsealpha.db"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12"))

NEWS_SCHEDULER_ENABLED = os.getenv("NEWS_SCHEDULER_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
NEWS_SCHEDULER_INTERVAL_MINUTES = int(os.getenv("NEWS_SCHEDULER_INTERVAL_MINUTES", "60"))
NEWS_SCHEDULER_RUN_ON_START = os.getenv("NEWS_SCHEDULER_RUN_ON_START", "true").strip().lower() in {"1", "true", "yes", "on"}
