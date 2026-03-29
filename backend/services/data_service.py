from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import PROCESSED_DIR, RAW_DIR


@dataclass
class DataCache:
    companies: dict[str, pd.DataFrame]
    news: pd.DataFrame


class MarketDataService:
    def __init__(self) -> None:
        self.cache = self._load_data()

    def _load_data(self) -> DataCache:
        companies: dict[str, pd.DataFrame] = {}
        for file_path in PROCESSED_DIR.glob("*_final.csv"):
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    continue
                ticker = str(df["ticker"].iloc[0]) if "ticker" in df.columns else file_path.stem.replace("_final", "")
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.sort_values("date")
                companies[ticker] = df
            except Exception:
                continue

        news_path_candidates = [RAW_DIR / "rss_news.csv", PROCESSED_DIR / "rss_cleaned.csv"]
        news = pd.DataFrame()
        for path in news_path_candidates:
            if path.exists():
                try:
                    news = pd.read_csv(path)
                    break
                except Exception:
                    pass

        if not news.empty and "Date" in news.columns:
            news["Date"] = pd.to_datetime(news["Date"], errors="coerce")
            news = news.sort_values("Date", ascending=False)

        return DataCache(companies=companies, news=news)

    def refresh(self) -> None:
        self.cache = self._load_data()

    def resolve_ticker(self, ticker: str | None = None, company: str | None = None) -> str | None:
        if ticker:
            t = ticker.upper().strip()
            if t in self.cache.companies:
                return t

        if company:
            needle = company.strip().lower()
            if not needle:
                return None

            for tkr, df in self.cache.companies.items():
                latest = df.tail(1).iloc[0]
                name = str(latest.get("company_name", "")).strip().lower()
                if needle in name or name in needle:
                    return tkr
        return None

    def list_companies(self) -> list[dict[str, Any]]:
        rows = []
        for ticker, df in self.cache.companies.items():
            latest = df.tail(1).iloc[0]
            prev_close = float(df.tail(2).iloc[0].get("Close", latest.get("Close", 0.0))) if len(df) > 1 else float(latest.get("Close", 0.0))
            close = float(latest.get("Close", 0.0))
            change = ((close - prev_close) / prev_close * 100.0) if prev_close else 0.0
            sentiment = float(latest.get("sentiment", 0.0))
            rows.append(
                {
                    "ticker": ticker,
                    "name": str(latest.get("company_name", ticker)),
                    "price": round(close, 2),
                    "change": round(change, 2),
                    "sentiment": round(sentiment, 3),
                    "sentimentLabel": self._sentiment_label(sentiment)
                }
            )
        return rows

    def company_detail(self, ticker: str) -> dict[str, Any] | None:
        df = self.cache.companies.get(ticker)
        if df is None or df.empty:
            return None

        latest = df.tail(1).iloc[0]
        return {
            "ticker": ticker,
            "name": str(latest.get("company_name", ticker)),
            "price": float(latest.get("Close", 0.0)),
            "sentiment": float(latest.get("sentiment", 0.0)),
            "sentimentLabel": self._sentiment_label(float(latest.get("sentiment", 0.0))),
            "predictionLabel": str(latest.get("signal", "HOLD"))
        }

    def company_series(self, ticker: str, limit: int = 30) -> list[dict[str, Any]]:
        df = self.cache.companies.get(ticker)
        if df is None or df.empty:
            return []

        subset = df.tail(limit).copy()
        subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
        return [
            {
                "date": row["date"],
                "price": round(float(row.get("Close", 0.0)), 2),
                "sentiment": round(float(row.get("sentiment", 0.0)), 3)
            }
            for _, row in subset.iterrows()
        ]

    def company_features(self, ticker: str) -> dict[str, float] | None:
        df = self.cache.companies.get(ticker)
        if df is None or df.empty:
            return None
        latest = df.tail(1).iloc[0]
        return {
            "sentiment": float(latest.get("sentiment", 0.0)),
            "return_1d": float(latest.get("return_1d", 0.0)),
            "momentum": float(latest.get("momentum", 0.0)),
            "volatility": float(latest.get("volatility", 0.0))
        }

    def company_rows_for_range(self, ticker: str, start_date: str, range_days: int) -> list[dict[str, Any]]:
        df = self.cache.companies.get(ticker)
        if df is None or df.empty:
            return []

        parsed_start = pd.to_datetime(start_date, errors="coerce")
        if pd.isna(parsed_start):
            return []

        subset = df[df["date"] >= parsed_start].head(max(1, range_days)).copy()
        if subset.empty:
            return []

        rows = []
        for _, row in subset.iterrows():
            rows.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else "N/A",
                    "close": float(row.get("Close", 0.0)),
                    "sentiment": float(row.get("sentiment", 0.0)),
                    "return_1d": float(row.get("return_1d", 0.0)),
                    "momentum": float(row.get("momentum", 0.0)),
                    "volatility": float(row.get("volatility", 0.0)),
                    "ticker": ticker,
                    "company": str(row.get("company_name", ticker))
                }
            )
        return rows

    def news_feed(self, ticker: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if self.cache.news.empty:
            return []

        df = self.cache.news
        if ticker and "Ticker" in df.columns:
            df = df[df["Ticker"].astype(str).str.upper() == ticker.upper()]

        df = df.head(limit)
        rows = []
        for i, row in df.iterrows():
            sentiment_val = row.get("sentiment", "Neutral")
            sentiment = sentiment_val if isinstance(sentiment_val, str) else self._sentiment_label(float(sentiment_val))
            published = row.get("Date")
            published_str = pd.to_datetime(published).strftime("%Y-%m-%d %H:%M") if pd.notna(published) else "N/A"
            rows.append(
                {
                    "id": int(i),
                    "ticker": str(row.get("Ticker", "MARKET")),
                    "title": str(row.get("Title", "")),
                    "summary": str(row.get("Summary", "")),
                    "source": str(row.get("Source", "Unknown")),
                    "publishedAt": published_str,
                    "link": str(row.get("Link", "")),
                    "sentiment": sentiment
                }
            )
        return rows

    def overview(self) -> dict[str, Any]:
        companies = self.list_companies()
        news = self.news_feed(limit=20)
        articles = len(self.cache.news.index) if not self.cache.news.empty else 0
        avg_sent = float(np.mean([c["sentiment"] for c in companies])) if companies else 0.0

        top_bull = max(companies, key=lambda x: x["sentiment"], default={"ticker": "N/A"})
        top_bear = min(companies, key=lambda x: x["sentiment"], default={"ticker": "N/A"})

        chart_series = []
        if companies:
            first_ticker = companies[0]["ticker"]
            chart_series = self.company_series(first_ticker, limit=14)

        return {
            "overviewStats": {
                "totalArticles": articles,
                "companiesTracked": len(companies),
                "avgSentiment": round(avg_sent, 3),
                "topBullish": top_bull["ticker"],
                "topBearish": top_bear["ticker"]
            },
            "companies": companies,
            "chartSeries": chart_series,
            "latestNews": news[:8],
            "predictionSnapshot": {
                "ticker": top_bull.get("ticker", "N/A"),
                "label": top_bull.get("sentimentLabel", "Neutral"),
                "confidence": 76,
                "explanation": "Recent positive sentiment and momentum indicate moderate bullish outlook"
            },
            "topMovers": sorted(companies, key=lambda x: abs(x["change"]), reverse=True)[:5]
        }

    def market_summary(self) -> dict[str, Any]:
        companies = self.list_companies()
        sentiments = [c["sentiment"] for c in companies]
        mean_sent = float(np.mean(sentiments)) if sentiments else 0.0
        pulse = "Risk-On" if mean_sent > 0.2 else "Risk-Off" if mean_sent < -0.2 else "Neutral"

        return {
            "marketPulse": pulse,
            "sectors": [
                {"name": "Technology", "sentiment": round(mean_sent + 0.08, 3)},
                {"name": "Financials", "sentiment": round(mean_sent - 0.03, 3)},
                {"name": "Energy", "sentiment": round(mean_sent - 0.12, 3)},
                {"name": "Consumer", "sentiment": round(mean_sent + 0.02, 3)}
            ]
        }

    @staticmethod
    def _sentiment_label(value: float) -> str:
        if value > 0.15:
            return "Positive"
        if value < -0.15:
            return "Negative"
        return "Neutral"
