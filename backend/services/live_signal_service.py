from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from ..config import PROJECT_ROOT, RAW_DIR
from ..db import get_connection


@dataclass
class NewsContext:
    ticker: str
    lookback_days: int
    total_news: int
    today_news: int
    latest_published_at: str | None
    latest_age_minutes: int | None
    has_latest_hour_report: bool
    aggregate_sentiment: float
    refresh_triggered: bool
    refresh_reason: str | None


class LiveSignalService:
    """Builds live sentiment-aware features for model prediction.

    This extends existing architecture by:
    - Combining ticker-specific DB + CSV news
    - Aggregating sentiment from today and previous days (lookback window)
    - Checking freshness of latest news (default 1 hour)
    - Triggering background refresh when stale (non-blocking)
    """

    def __init__(self) -> None:
        self.refresh_cooldown_minutes = 15
        self.latest_required_minutes = 60
        self.default_lookback_days = 30
        self._last_refresh_triggered_at: datetime | None = None

    def enrich_features_with_news(
        self,
        ticker: str,
        base_features: dict[str, float] | None,
        csv_news_rows: list[dict[str, Any]],
    ) -> tuple[dict[str, float], NewsContext]:
        ticker_upper = str(ticker or "").upper().strip()
        features = dict(base_features or {})

        db_news = self._get_db_news_for_ticker(ticker_upper, limit=400)
        merged_news = self._merge_and_filter_news(ticker_upper, csv_news_rows, db_news, self.default_lookback_days)

        aggregate_sentiment = self._aggregate_sentiment_score(merged_news)
        latest_dt = self._latest_timestamp(merged_news)
        now_utc = datetime.now(timezone.utc)

        latest_age_minutes = None
        has_latest_hour_report = False
        if latest_dt is not None:
            latest_age_minutes = max(0, int((now_utc - latest_dt).total_seconds() // 60))
            has_latest_hour_report = latest_age_minutes <= self.latest_required_minutes

        refresh_triggered = False
        refresh_reason = None
        if not has_latest_hour_report:
            refresh_triggered, refresh_reason = self._trigger_background_news_refresh(ticker_upper)

        today_count = self._count_today_news(merged_news)

        if merged_news:
            features["sentiment"] = aggregate_sentiment

        context = NewsContext(
            ticker=ticker_upper,
            lookback_days=self.default_lookback_days,
            total_news=len(merged_news),
            today_news=today_count,
            latest_published_at=latest_dt.isoformat().replace("+00:00", "Z") if latest_dt else None,
            latest_age_minutes=latest_age_minutes,
            has_latest_hour_report=has_latest_hour_report,
            aggregate_sentiment=round(float(aggregate_sentiment), 4),
            refresh_triggered=refresh_triggered,
            refresh_reason=refresh_reason,
        )
        return features, context

    def _get_db_news_for_ticker(self, ticker: str, limit: int = 200) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, ticker, title, summary, sentiment, published_at, created_at
                FROM market_news
                WHERE UPPER(COALESCE(ticker, '')) = ?
                ORDER BY published_at DESC, created_at DESC
                LIMIT ?
                """,
                (ticker, max(1, int(limit))),
            ).fetchall()

        output: list[dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "id": int(row["id"]),
                    "ticker": row["ticker"] or ticker,
                    "title": row["title"] or "",
                    "summary": row["summary"] or "",
                    "sentiment": row["sentiment"] or "Neutral",
                    "publishedAt": row["published_at"] or row["created_at"],
                }
            )
        return output

    def _merge_and_filter_news(
        self,
        ticker: str,
        csv_news_rows: list[dict[str, Any]],
        db_news_rows: list[dict[str, Any]],
        lookback_days: int,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, lookback_days))
        merged = []

        for row in list(db_news_rows) + list(csv_news_rows):
            row_ticker = str(row.get("ticker", row.get("Ticker", ""))).upper().strip()
            if row_ticker and row_ticker != ticker:
                continue

            published = row.get("publishedAt", row.get("published_at", row.get("Date")))
            published_dt = self._parse_datetime(published)
            if published_dt is None or published_dt < cutoff:
                continue

            merged.append(
                {
                    "title": str(row.get("title", row.get("Title", "")))[:500],
                    "summary": str(row.get("summary", row.get("Summary", "")))[:1000],
                    "sentiment": row.get("sentiment", "Neutral"),
                    "publishedAt": published_dt,
                }
            )

        merged.sort(key=lambda x: x["publishedAt"], reverse=True)
        return merged

    def _aggregate_sentiment_score(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0

        values: list[float] = []
        for row in rows:
            values.append(self._sentiment_to_score(row.get("sentiment")))

        if not values:
            return 0.0
        return float(sum(values) / len(values))

    def _sentiment_to_score(self, raw: Any) -> float:
        if raw is None:
            return 0.0

        if isinstance(raw, (int, float)):
            return float(max(-1.0, min(1.0, raw)))

        text = str(raw).strip().lower()
        if not text:
            return 0.0

        if "positive" in text or "bull" in text or text == "buy":
            return 0.6
        if "negative" in text or "bear" in text or text == "sell":
            return -0.6
        if "neutral" in text or text == "hold":
            return 0.0

        # Mild lexical fallback when sentiment label is unavailable.
        positive_words = ("beat", "growth", "surge", "strong", "up", "gain")
        negative_words = ("miss", "fall", "drop", "weak", "down", "loss")
        score = 0.0
        for word in positive_words:
            if word in text:
                score += 0.1
        for word in negative_words:
            if word in text:
                score -= 0.1
        return float(max(-1.0, min(1.0, score)))

    def _latest_timestamp(self, rows: list[dict[str, Any]]) -> datetime | None:
        if not rows:
            return None
        latest = rows[0].get("publishedAt")
        if isinstance(latest, datetime):
            return latest
        return self._parse_datetime(latest)

    def _count_today_news(self, rows: list[dict[str, Any]]) -> int:
        today = datetime.now(timezone.utc).date()
        count = 0
        for row in rows:
            dt = row.get("publishedAt")
            if isinstance(dt, datetime) and dt.date() == today:
                count += 1
        return count

    def _trigger_background_news_refresh(self, ticker: str) -> tuple[bool, str | None]:
        now_utc = datetime.now(timezone.utc)
        if self._last_refresh_triggered_at is not None:
            delta = now_utc - self._last_refresh_triggered_at
            if delta < timedelta(minutes=self.refresh_cooldown_minutes):
                return False, f"refresh skipped: cooldown {self.refresh_cooldown_minutes}m"

        script_path = PROJECT_ROOT / "rss_news_pipeline.py"
        if not script_path.exists():
            return False, "refresh skipped: rss_news_pipeline.py not found"

        try:
            # Non-blocking trigger so API latency remains low.
            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._last_refresh_triggered_at = now_utc
            return True, f"refresh triggered for stale report ({ticker})"
        except Exception as exc:  # pragma: no cover
            return False, f"refresh failed: {exc}"

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)

        text = str(value).strip()
        if not text or text == "N/A":
            return None

        parsed = pd.to_datetime(text, errors="coerce", utc=True)
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime().astimezone(timezone.utc)

    def file_news_health(self) -> dict[str, Any]:
        rss_path = RAW_DIR / "rss_news.csv"
        if not rss_path.exists():
            return {
                "exists": False,
                "latestFileUpdate": None,
                "latestAgeMinutes": None,
                "freshWithinHour": False,
            }

        modified = datetime.fromtimestamp(rss_path.stat().st_mtime, tz=timezone.utc)
        age_minutes = max(0, int((datetime.now(timezone.utc) - modified).total_seconds() // 60))
        return {
            "exists": True,
            "latestFileUpdate": modified.isoformat().replace("+00:00", "Z"),
            "latestAgeMinutes": age_minutes,
            "freshWithinHour": age_minutes <= self.latest_required_minutes,
        }
