from __future__ import annotations

import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import PROJECT_ROOT, RAW_DIR
from ..db import get_connection, now_iso
from .news_sentiment_service import NewsSentimentService


class NewsSchedulerService:
    """Hourly scheduler for RSS scrape + sentiment + verdict ingestion."""

    def __init__(self, interval_minutes: int = 60, run_on_start: bool = True) -> None:
        self.interval_minutes = max(5, int(interval_minutes))
        self.run_on_start = bool(run_on_start)
        self._sentiment = NewsSentimentService()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._running = False
        self._last_run_started_at: str | None = None
        self._last_run_finished_at: str | None = None
        self._last_run_status: str = "idle"
        self._last_run_message: str = "not started"

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name="news-hourly-scheduler")
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._running = False

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "intervalMinutes": self.interval_minutes,
            "lastRunStartedAt": self._last_run_started_at,
            "lastRunFinishedAt": self._last_run_finished_at,
            "lastRunStatus": self._last_run_status,
            "lastRunMessage": self._last_run_message,
        }

    def _loop(self) -> None:
        if self.run_on_start:
            self._run_once()

        sleep_seconds = self.interval_minutes * 60
        while not self._stop_event.wait(timeout=sleep_seconds):
            self._run_once()

    def _run_once(self) -> None:
        if self._stop_event.is_set():
            return

        self._last_run_started_at = now_iso()
        self._last_run_status = "running"
        self._last_run_message = "scheduler cycle started"

        try:
            self._run_rss_scraper()
            inserted = self._ingest_latest_rss_to_market_news(limit=1000)
            self._last_run_status = "ok"
            self._last_run_message = f"completed; inserted {inserted} rows"
        except Exception as exc:  # pragma: no cover
            self._last_run_status = "error"
            self._last_run_message = str(exc)
        finally:
            self._last_run_finished_at = now_iso()

    def _run_rss_scraper(self) -> None:
        script_path = PROJECT_ROOT / "rss_news_pipeline.py"
        if not script_path.exists():
            raise FileNotFoundError(f"rss pipeline not found: {script_path}")

        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=50 * 60,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"rss pipeline failed with exit code {proc.returncode}")

    def _ingest_latest_rss_to_market_news(self, limit: int = 1000) -> int:
        csv_path = RAW_DIR / "rss_news.csv"
        if not csv_path.exists():
            return 0

        df = pd.read_csv(csv_path)
        if df.empty:
            return 0

        # Keep most recent rows for each run to minimize DB scan pressure.
        if "Date" in df.columns:
            parsed_dates = pd.to_datetime(df["Date"], errors="coerce", utc=True)
            df = df.assign(_parsed_date=parsed_dates).sort_values("_parsed_date", ascending=False)
        df = df.head(max(50, int(limit))).copy()

        inserted = 0
        with get_connection() as conn:
            existing = {
                (str(r["title"] or "").strip(), str(r["link"] or "").strip())
                for r in conn.execute("SELECT title, link FROM market_news ORDER BY id DESC LIMIT 8000").fetchall()
            }

            for _, row in df.iterrows():
                title = str(row.get("Title", "")).strip()
                summary = str(row.get("Summary", "")).strip()
                link = str(row.get("Link", "")).strip()
                key = (title, link)

                if not title or key in existing:
                    continue

                sentiment = self._sentiment.analyze_news(title=title, summary=summary)
                verdict = self._sentiment.verdict_from_sentiment(float(sentiment.get("score", 0.0)))
                sentiment_label = str(sentiment.get("label", "Neutral")).strip() or "Neutral"
                sentiment_source = str(sentiment.get("source", "unknown")).strip() or "unknown"

                # Persist verdict/source into summary tail to preserve current schema without migrations.
                enriched_summary = summary
                suffix = f"\n\n[sentiment_source={sentiment_source}; verdict={verdict}]"
                if suffix not in enriched_summary:
                    enriched_summary = (enriched_summary + suffix).strip()

                conn.execute(
                    """
                    INSERT INTO market_news(ticker, company, title, summary, source, link, sentiment, published_at, created_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(row.get("Ticker", "")).strip().upper() or None,
                        str(row.get("Company", "")).strip() or None,
                        title,
                        enriched_summary[:4000] if enriched_summary else None,
                        str(row.get("Source", "Google News RSS")).strip() or "Google News RSS",
                        link or None,
                        sentiment_label,
                        str(row.get("Date", "")).strip() or now_iso(),
                        now_iso(),
                    ),
                )
                existing.add(key)
                inserted += 1

            conn.commit()

        return inserted


_scheduler_instance: NewsSchedulerService | None = None


def get_news_scheduler(interval_minutes: int = 60, run_on_start: bool = True) -> NewsSchedulerService:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NewsSchedulerService(interval_minutes=interval_minutes, run_on_start=run_on_start)
    return _scheduler_instance
