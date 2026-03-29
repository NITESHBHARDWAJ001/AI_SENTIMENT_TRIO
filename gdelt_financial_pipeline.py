"""
GDELT financial news -> sentiment -> Yahoo merge pipeline.

What this script does:
- Fetches financial-impact news from GDELT Doc API for configured companies/domains.
- Stores all GDELT data under data/gdelt/ (raw, processed, reports).
- Computes sentiment (FinBERT, then VADER, then keyword fallback).
- Aggregates daily sentiment by ticker.
- Merges sentiment with Yahoo stock data from data/raw/{ticker}_stock.csv.
- Generates BUY/SELL/HOLD signals and saves per-ticker and master outputs.

Run:
    python gdelt_financial_pipeline.py
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

try:
    from transformers import pipeline as hf_pipeline
    HAS_FINBERT = True
except ImportError:
    HAS_FINBERT = False

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk

    try:
        nltk.data.find("sentiment/vader_lexicon")
    except LookupError:
        nltk.download("vader_lexicon", quiet=True)
    HAS_VADER = True
except ImportError:
    HAS_VADER = False

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


TICKERS: List[str] = [
    "TSLA", "AAPL", "GOOGL", "MSFT",
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
]

COMPANY_MAP: Dict[str, str] = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta",
    "JPM": "JPMorgan",
    "XOM": "ExxonMobil",
    "WMT": "Walmart",
    "RELIANCE.NS": "Reliance",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
}

DOMAIN_MAP: Dict[str, List[str]] = {
    "RELIANCE.NS": ["oil", "gas", "energy", "jio"],
    "TSLA": ["ev", "electric vehicle", "battery", "elon musk"],
    "AAPL": ["iphone", "ios", "apple"],
    "MSFT": ["cloud", "azure", "ai"],
    "GOOGL": ["search", "ads", "ai"],
    "AMZN": ["ecommerce", "aws", "cloud"],
    "NVDA": ["ai", "gpu", "chips"],
    "META": ["social media", "ads"],
    "JPM": ["bank", "interest rate"],
    "XOM": ["oil", "crude", "energy"],
    "WMT": ["retail", "consumer"],
    "TCS.NS": ["it", "software", "outsourcing"],
    "INFY.NS": ["it", "consulting"],
    "HDFCBANK.NS": ["banking", "loan"],
    "ICICIBANK.NS": ["banking", "finance"],
}

FINANCIAL_TERMS: List[str] = [
    "stock", "shares", "earnings", "revenue", "profit", "guidance", "market", "finance",
]

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
LOOKBACK_DAYS = 730
WINDOW_DAYS = 30
MAX_RECORDS_PER_QUERY = 250

RAW_STOCK_DIR = Path("data/raw")
GDELT_DIR = Path("data/gdelt")
GDELT_RAW_DIR = GDELT_DIR / "raw"
GDELT_PROCESSED_DIR = GDELT_DIR / "processed"
GDELT_REPORTS_DIR = GDELT_DIR / "reports"

BUY_THRESHOLD = 0.2
SELL_THRESHOLD = -0.2

_FINBERT_PIPE = None
_VADER_ANALYZER = None


def _ensure_dirs() -> None:
    GDELT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    GDELT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GDELT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _iter_with_progress(items: List[str], desc: str):
    if tqdm is not None:
        return tqdm(items, desc=desc, unit="ticker")
    return items


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _contains_term(text: str, term: str) -> bool:
    term = re.escape(term.lower().strip())
    if not term:
        return False
    return re.search(rf"\b{term}\b", (text or "").lower()) is not None


def _gdelt_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


def generate_gdelt_queries(ticker: str, company: str) -> List[Tuple[str, str]]:
    queries: List[Tuple[str, str]] = []

    # Company-centric financial queries.
    queries.append((f'"{company}" AND ({" OR ".join(FINANCIAL_TERMS)})', "company_financial"))
    queries.append((f'"{ticker}" AND (stock OR earnings OR market)', "ticker_financial"))

    # Domain keywords tied to financial impact terms.
    for kw in DOMAIN_MAP.get(ticker, []):
        queries.append((f'"{company}" AND "{kw}" AND (market OR earnings OR revenue OR stock)', "company_domain_financial"))
        queries.append((f'"{kw}" AND (industry OR market OR stock)', "domain_market"))

    # De-duplicate preserving order.
    seen = set()
    deduped: List[Tuple[str, str]] = []
    for q, qt in queries:
        key = (q.lower().strip(), qt)
        if key not in seen:
            seen.add(key)
            deduped.append((q, qt))
    return deduped


def fetch_gdelt_news(
    query: str,
    query_type: str,
    ticker: str,
    company: str,
    lookback_days: int = LOOKBACK_DAYS,
    window_days: int = WINDOW_DAYS,
    max_records: int = MAX_RECORDS_PER_QUERY,
) -> List[Dict[str, str]]:
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    start_utc = (now_utc - timedelta(days=lookback_days)).replace(microsecond=0)

    if window_days <= 0:
        window_days = 30

    rows: List[Dict[str, str]] = []

    # Pull in time windows to improve long-range coverage for 2-year collection.
    window_start = start_utc
    while window_start < now_utc:
        window_end = min(window_start + timedelta(days=window_days), now_utc)
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "sort": "DateDesc",
            "maxrecords": str(max_records),
            "startdatetime": _gdelt_dt(window_start),
            "enddatetime": _gdelt_dt(window_end),
        }

        try:
            response = requests.get(GDELT_DOC_API, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            articles = payload.get("articles", [])

            for a in articles:
                title = _normalize_spaces(a.get("title", ""))
                if not title:
                    continue

                url = _normalize_spaces(a.get("url", ""))
                if not url:
                    continue

                seendate = pd.to_datetime(a.get("seendate", ""), utc=True, errors="coerce")
                if pd.isna(seendate):
                    continue

                rows.append(
                    {
                        "ticker": ticker,
                        "company_name": company,
                        "query": query,
                        "query_type": query_type,
                        "title": title,
                        "summary": _normalize_spaces(a.get("socialimage", "")),
                        "source_domain": _normalize_spaces(a.get("domain", "")),
                        "source_country": _normalize_spaces(a.get("sourcecountry", "")),
                        "language": _normalize_spaces(a.get("language", "")),
                        "published": seendate.strftime("%Y-%m-%d %H:%M:%S"),
                        "url": url,
                    }
                )
        except Exception as exc:
            print(
                f"[WARN] GDELT query failed for {ticker} ({query_type}) "
                f"window {window_start.date()}..{window_end.date()}: {exc}"
            )

        window_start = window_end

    return rows


def deduplicate_news(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    out["title"] = out["title"].fillna("").astype(str).str.strip()
    out["url"] = out["url"].fillna("").astype(str).str.strip()

    out = out[(out["title"] != "") & (out["url"] != "")]
    out = out.drop_duplicates(subset=["ticker", "url"]).drop_duplicates(subset=["ticker", "title"])

    out["published"] = pd.to_datetime(out["published"], errors="coerce")
    out = out.dropna(subset=["published"])
    out["date"] = out["published"].dt.strftime("%Y-%m-%d")

    return out.reset_index(drop=True)


def _get_finbert_pipe():
    global _FINBERT_PIPE
    if _FINBERT_PIPE is None and HAS_FINBERT:
        try:
            _FINBERT_PIPE = hf_pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception:
            _FINBERT_PIPE = None
    return _FINBERT_PIPE


def _get_vader_analyzer():
    global _VADER_ANALYZER
    if _VADER_ANALYZER is None and HAS_VADER:
        try:
            _VADER_ANALYZER = SentimentIntensityAnalyzer()
        except Exception:
            _VADER_ANALYZER = None
    return _VADER_ANALYZER


def compute_sentiment(text: str) -> float:
    if not text or not text.strip():
        return 0.0

    finbert = _get_finbert_pipe()
    if finbert is not None:
        try:
            result = finbert(text[:512])
            label = result[0]["label"].lower()
            score = float(result[0]["score"])
            if "positive" in label:
                return score
            if "negative" in label:
                return -score
            return 0.0
        except Exception:
            pass

    vader = _get_vader_analyzer()
    if vader is not None:
        try:
            return float(vader.polarity_scores(text)["compound"])
        except Exception:
            pass

    pos_words = {"gain", "bull", "rise", "surge", "profit", "strong", "beat"}
    neg_words = {"loss", "bear", "fall", "drop", "weak", "miss", "risk"}

    text_l = text.lower()
    pos = sum(1 for w in pos_words if _contains_term(text_l, w))
    neg = sum(1 for w in neg_words if _contains_term(text_l, w))
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def add_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    sentiment_values: List[float] = []
    iterator = out.iterrows()
    if tqdm is not None:
        iterator = tqdm(out.iterrows(), total=len(out), desc="Sentiment", unit="article")

    for _, row in iterator:
        text = f"{row.get('title', '')} {row.get('summary', '')}"
        sentiment_values.append(compute_sentiment(text))

    out["sentiment"] = pd.to_numeric(sentiment_values, errors="coerce").fillna(0.0)
    return out


def aggregate_daily_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["ticker", "date", "sentiment", "sentiment_std", "article_count"])

    agg = (
        df.groupby(["ticker", "date"], as_index=False)
        .agg(
            sentiment=("sentiment", "mean"),
            sentiment_std=("sentiment", "std"),
            article_count=("sentiment", "count"),
        )
        .sort_values(["ticker", "date"]) 
        .reset_index(drop=True)
    )
    agg["sentiment_std"] = agg["sentiment_std"].fillna(0.0)
    agg["sentiment"] = agg["sentiment"].round(4)
    agg["sentiment_std"] = agg["sentiment_std"].round(4)
    return agg


def load_stock_data(ticker: str) -> pd.DataFrame:
    path = RAW_STOCK_DIR / f"{ticker}_stock.csv"
    if not path.exists():
        print(f"[WARN] Stock file missing for {ticker}: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    if "Date" not in df.columns or "Close" not in df.columns:
        print(f"[WARN] Missing Date/Close in stock file for {ticker}")
        return pd.DataFrame()

    out = df[["Date", "Close"]].copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    out = out.dropna(subset=["Date", "Close"]).drop_duplicates(subset=["Date"])
    return out.sort_values("Date").reset_index(drop=True)


def infer_stock_lookback_days(ticker: str, fallback_days: int = LOOKBACK_DAYS) -> int:
    """
    Infer scrape lookback from Yahoo stock span for a ticker.

    This keeps GDELT collection aligned with the stock date coverage used
    during merge. Falls back to LOOKBACK_DAYS when stock dates are unavailable.
    """
    stock_df = load_stock_data(ticker)
    if stock_df.empty:
        return fallback_days

    dates = pd.to_datetime(stock_df["Date"], errors="coerce")
    dates = dates.dropna()
    if dates.empty:
        return fallback_days

    min_date = dates.min()
    max_date = dates.max()
    span_days = int((max_date - min_date).days)
    if span_days <= 0:
        return fallback_days

    # Ensure at least the configured 2-year horizon.
    return max(fallback_days, span_days)


def add_stock_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    out["return_1d"] = out["Close"].pct_change()
    out["return_5d"] = out["Close"].pct_change(periods=5)
    out["momentum"] = out["Close"] - out["Close"].shift(5)
    out["volatility"] = out["return_1d"].rolling(window=5, min_periods=5).std()
    return out


def merge_with_stock(stock_df: pd.DataFrame, sent_df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if stock_df.empty:
        return pd.DataFrame()

    merged = stock_df.copy()
    merged["date"] = merged["Date"]
    merged = merged[["date", "Close", "return_1d", "return_5d", "momentum", "volatility"]]
    merged["ticker"] = ticker

    if sent_df.empty:
        merged["sentiment"] = 0.0
        merged["sentiment_std"] = 0.0
        merged["article_count"] = 0
        merged["sentiment_source"] = "default"
        return merged

    s = sent_df[sent_df["ticker"] == ticker].copy()
    result = merged.merge(
        s[["date", "sentiment", "sentiment_std", "article_count"]],
        on="date",
        how="left",
    )

    has_news = result["article_count"].notna() & (result["article_count"] > 0)
    result["sentiment"] = result["sentiment"].fillna(0.0)
    result["sentiment_std"] = result["sentiment_std"].fillna(0.0)
    result["article_count"] = result["article_count"].fillna(0).astype(int)
    result["sentiment_source"] = np.where(has_news, "gdelt", "default")

    return result


def compute_signal(sentiment: float, return_1d: float, momentum: float, volatility: float) -> Tuple[str, float, float]:
    sentiment = 0.0 if pd.isna(sentiment) else float(sentiment)
    return_1d = 0.0 if pd.isna(return_1d) else float(return_1d)
    momentum = 0.0 if pd.isna(momentum) else float(momentum)
    volatility = 0.0 if pd.isna(volatility) else float(volatility)

    score = 0.6 * sentiment + 0.25 * return_1d + 0.15 * momentum

    if score > BUY_THRESHOLD:
        signal = "BUY"
    elif score < SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = abs(sentiment) * max(0.0, 1.0 - volatility)
    confidence = max(0.0, min(1.0, confidence))
    return signal, score, confidence


def run_pipeline(lookback_days: int = LOOKBACK_DAYS) -> None:
    _ensure_dirs()
    all_raw_rows: List[Dict[str, str]] = []

    print("[INFO] Starting GDELT financial scraping...")
    for ticker in _iter_with_progress(TICKERS, "GDELT scrape"):
        company = COMPANY_MAP[ticker]
        ticker_lookback_days = infer_stock_lookback_days(ticker, fallback_days=lookback_days)
        queries = generate_gdelt_queries(ticker, company)
        print(
            f"\n[INFO] Scraping {ticker} ({company}) with {len(queries)} GDELT queries "
            f"across {ticker_lookback_days} days ({WINDOW_DAYS}-day windows)..."
        )

        ticker_rows: List[Dict[str, str]] = []
        for query, query_type in queries:
            rows = fetch_gdelt_news(
                query=query,
                query_type=query_type,
                ticker=ticker,
                company=company,
                lookback_days=ticker_lookback_days,
                window_days=WINDOW_DAYS,
                max_records=MAX_RECORDS_PER_QUERY,
            )
            ticker_rows.extend(rows)
            print(f"  [OK] {query_type}: {len(rows)} articles")

        ticker_df = deduplicate_news(pd.DataFrame(ticker_rows))
        print(f"  [INFO] {ticker}: {len(ticker_rows)} raw -> {len(ticker_df)} deduped")

        ticker_raw_path = GDELT_RAW_DIR / f"{ticker}_gdelt_news.csv"
        ticker_df.to_csv(ticker_raw_path, index=False, encoding="utf-8")
        print(f"  [OK] Saved raw ticker news: {ticker_raw_path}")

        all_raw_rows.extend(ticker_df.to_dict(orient="records"))

    all_news_df = pd.DataFrame(all_raw_rows)
    if all_news_df.empty:
        print("[WARN] No GDELT news collected. Exiting.")
        return

    archive_path = GDELT_RAW_DIR / "gdelt_news_archive.csv"
    all_news_df.to_csv(archive_path, index=False, encoding="utf-8")
    print(f"\n[OK] Saved GDELT archive: {archive_path}")

    print("\n[INFO] Computing sentiment on GDELT articles...")
    sent_news_df = add_sentiment(all_news_df)
    sent_articles_path = GDELT_PROCESSED_DIR / "gdelt_news_with_sentiment.csv"
    sent_news_df.to_csv(sent_articles_path, index=False, encoding="utf-8")
    print(f"[OK] Saved article-level sentiment: {sent_articles_path}")

    daily_sent_df = aggregate_daily_sentiment(sent_news_df)
    daily_sent_path = GDELT_PROCESSED_DIR / "gdelt_daily_sentiment.csv"
    daily_sent_df.to_csv(daily_sent_path, index=False, encoding="utf-8")
    print(f"[OK] Saved daily sentiment: {daily_sent_path}")

    print("\n[INFO] Merging GDELT sentiment with Yahoo stock data...")
    per_ticker_frames: List[pd.DataFrame] = []
    for ticker in _iter_with_progress(TICKERS, "Merge"):
        company = COMPANY_MAP[ticker]
        stock_df = add_stock_features(load_stock_data(ticker))
        if stock_df.empty:
            continue

        merged = merge_with_stock(stock_df, daily_sent_df, ticker)
        if merged.empty:
            continue

        signals = [
            compute_signal(row.sentiment, row.return_1d, row.momentum, row.volatility)
            for row in merged.itertuples(index=False)
        ]
        merged[["signal", "score", "confidence"]] = pd.DataFrame(signals, index=merged.index)
        merged["company_name"] = company

        merged = merged[
            [
                "date", "ticker", "company_name", "Close", "sentiment", "sentiment_std",
                "return_1d", "return_5d", "momentum", "volatility", "score",
                "signal", "confidence", "article_count", "sentiment_source",
            ]
        ]

        out_path = GDELT_PROCESSED_DIR / f"{ticker}_gdelt_final.csv"
        merged.to_csv(out_path, index=False, encoding="utf-8")
        coverage = 100.0 * (merged["sentiment_source"] == "gdelt").sum() / len(merged)
        print(f"[OK] Saved {ticker} merged: {out_path} | Coverage: {coverage:.1f}%")

        per_ticker_frames.append(merged)

    if not per_ticker_frames:
        print("[WARN] No merged ticker datasets were generated.")
        return

    master_df = pd.concat(per_ticker_frames, ignore_index=True).sort_values(["ticker", "date"]).reset_index(drop=True)
    master_csv = GDELT_REPORTS_DIR / "gdelt_sentiment_master.csv"
    master_xlsx = GDELT_REPORTS_DIR / "gdelt_sentiment_master.xlsx"
    master_df.to_csv(master_csv, index=False, encoding="utf-8")
    print(f"\n[OK] Saved master CSV: {master_csv}")

    try:
        master_df.to_excel(master_xlsx, index=False)
        print(f"[OK] Saved master Excel: {master_xlsx}")
    except Exception as exc:
        print(f"[WARN] Could not save Excel report: {exc}")

    summary = {
        "rows_master": len(master_df),
        "rows_articles": len(sent_news_df),
        "tickers": master_df["ticker"].nunique(),
        "sources": sent_news_df["source_domain"].nunique() if "source_domain" in sent_news_df.columns else 0,
        "date_min": master_df["date"].min(),
        "date_max": master_df["date"].max(),
    }
    summary_path = GDELT_REPORTS_DIR / "gdelt_summary.csv"
    pd.DataFrame([summary]).to_csv(summary_path, index=False, encoding="utf-8")
    print(f"[OK] Saved summary: {summary_path}")


def main() -> None:
    print("[INFO] GDELT Financial Sentiment Pipeline")
    print("[INFO] Scrape -> sentiment -> Yahoo merge\n")
    run_pipeline(lookback_days=LOOKBACK_DAYS)
    print("\n[INFO] Pipeline completed.")


if __name__ == "__main__":
    main()
