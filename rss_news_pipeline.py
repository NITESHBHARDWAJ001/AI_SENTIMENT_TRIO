"""
Google News RSS scraping pipeline for stock market sentiment workflows.

Features:
- Fetches company and domain/sector news from Google News RSS (no API key)
- Uses rolling date-window query expansion for stronger long-range coverage
- Maps each article to a company ticker using direct and domain matching
- Cleans and deduplicates records
- Exports raw and processed datasets to CSV + master Excel file
"""

from __future__ import annotations

import re
from datetime import timedelta, timezone, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import feedparser
import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    tqdm = None


TICKERS: Dict[str, str] = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "RELIANCE.NS": "Reliance",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
}

DOMAIN_MAP: Dict[str, List[str]] = {
    "RELIANCE.NS": ["oil", "gas", "energy", "jio"],
    "TSLA": ["ev", "electric vehicle", "battery", "elon musk"],
    "AAPL": ["iphone", "ios", "apple"],
    "MSFT": ["cloud", "azure", "ai"],
    "GOOGL": ["search", "ads", "ai"],
    "TCS.NS": ["it", "software", "outsourcing"],
    "INFY.NS": ["it", "consulting"],
}

BASE_URL = "https://news.google.com/rss/search?q={}"
SOURCE_NAME = "Google News RSS"
DEFAULT_LOOKBACK_DAYS = 730
DEFAULT_WINDOW_DAYS = 30
DEFAULT_MAX_RESULTS_PER_QUERY = 50


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _contains_term(text: str, term: str) -> bool:
    """Match whole terms where possible, supporting multi-word phrases safely."""
    term = re.escape(term.lower().strip())
    if not term:
        return False
    pattern = rf"\b{term}\b"
    return re.search(pattern, text.lower()) is not None


def fetch_rss(query: str, max_results: int = 25) -> List[Dict[str, str]]:
    """
    Fetch and parse Google News RSS for a query.

    Args:
        query: Search string (e.g., 'Tesla stock OR earnings')
        max_results: Maximum number of entries to keep from feed

    Returns:
        List of article dicts containing title, link, published, summary, query_used
    """
    rss_url = BASE_URL.format(quote_plus(query))
    feed = feedparser.parse(rss_url)

    rows: List[Dict[str, str]] = []
    for entry in feed.entries[:max_results]:
        rows.append(
            {
                "title": _normalize_spaces(entry.get("title", "")),
                "link": _normalize_spaces(entry.get("link", "")),
                "published": _normalize_spaces(entry.get("published", "")),
                "summary": _normalize_spaces(entry.get("summary", "")),
                "query_used": query,
            }
        )
    return rows


def generate_time_window_queries(
    base_query: str,
    lookback_days: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> List[str]:
    """
    Build rolling date-window queries to improve historical RSS coverage.

    Google News RSS can miss older records when a query is broad.
    Splitting into smaller windows with after:/before: improves retrieval depth.
    """
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    start_utc = (now_utc - timedelta(days=lookback_days)).replace(microsecond=0)

    if window_days <= 0:
        window_days = DEFAULT_WINDOW_DAYS

    queries: List[str] = []
    window_start = start_utc
    while window_start < now_utc:
        window_end = min(window_start + timedelta(days=window_days), now_utc)
        after_date = window_start.strftime("%Y-%m-%d")
        before_date = window_end.strftime("%Y-%m-%d")
        queries.append(f"({base_query}) after:{after_date} before:{before_date}")
        window_start = window_end

    return queries


def map_company(
    text: str, preferred_ticker: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
        Map text to ticker/company with priority:
            1) Preferred ticker direct/domain match (when query context is company-wise)
            2) Global direct company-name/ticker match
            3) Global domain keyword match

    Returns:
        (ticker, company, mapped_type) where mapped_type in {'Direct', 'Domain'}
    """
    text_l = (text or "").lower()

    # When processing company-wise, prefer that company's own matching first.
    if preferred_ticker and preferred_ticker in TICKERS:
        preferred_company = TICKERS[preferred_ticker]
        if _contains_term(text_l, preferred_company.lower()) or _contains_term(
            text_l, preferred_ticker.lower()
        ):
            return preferred_ticker, preferred_company, "Direct"

        for kw in DOMAIN_MAP.get(preferred_ticker, []):
            if _contains_term(text_l, kw.lower()):
                return preferred_ticker, preferred_company, "Domain"

    # Global direct mapping by company name (plus ticker token fallback).
    for ticker, company in TICKERS.items():
        if _contains_term(text_l, company.lower()) or _contains_term(text_l, ticker.lower()):
            return ticker, company, "Direct"

    # Domain mapping by keywords.
    for ticker, keywords in DOMAIN_MAP.items():
        for kw in keywords:
            if _contains_term(text_l, kw.lower()):
                return ticker, TICKERS.get(ticker), "Domain"

    return None, None, None


def _iter_with_progress(items: Iterable[Tuple[str, str]], label: str):
    items = list(items)
    if tqdm is not None:
        return tqdm(items, desc=label, unit="query")
    return items


def build_dataset(
    max_results_per_query: int = DEFAULT_MAX_RESULTS_PER_QUERY,
    keep_unmapped: bool = False,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> pd.DataFrame:
    """
    Build end-to-end dataset from company-wise queries.

    Args:
        max_results_per_query: Limit entries fetched for each query
        keep_unmapped: Keep rows that cannot be mapped to a ticker
        lookback_days: Keep only articles published within the last N days
        window_days: Query slice size for rolling RSS retrieval

    Returns:
        Cleaned and mapped DataFrame ready for downstream sentiment analysis
    """
    all_rows: List[Dict[str, str]] = []

    company_items = list(TICKERS.items())

    print(f"[INFO] Fetching company-wise queries: {len(company_items)} companies")
    for ticker, company in _iter_with_progress(company_items, "Company-wise pipeline"):
        print(f"[INFO] Processing {ticker} ({company})")

        company_query = f"{company} stock OR shares OR earnings"
        print(f"[INFO] {ticker} | Company query: {company_query}")
        company_queries = generate_time_window_queries(
            company_query,
            lookback_days=lookback_days,
            window_days=window_days,
        )
        for sliced_query in company_queries:
            for row in fetch_rss(sliced_query, max_results=max_results_per_query):
                row["target_ticker"] = ticker
                row["target_company"] = company
                row["query_type"] = "Company"
                all_rows.append(row)

        for keyword in DOMAIN_MAP.get(ticker, []):
            domain_query = f"{keyword} market OR industry"
            print(f"[INFO] {ticker} | Domain query: {domain_query}")
            domain_queries = generate_time_window_queries(
                domain_query,
                lookback_days=lookback_days,
                window_days=window_days,
            )
            for sliced_query in domain_queries:
                for row in fetch_rss(sliced_query, max_results=max_results_per_query):
                    row["target_ticker"] = ticker
                    row["target_company"] = company
                    row["query_type"] = "Domain"
                    all_rows.append(row)

    if not all_rows:
        print("[WARN] No rows fetched from RSS feeds.")
        return pd.DataFrame(
            columns=[
                "Date",
                "Ticker",
                "Company",
                "Source",
                "Title",
                "Summary",
                "Link",
                "Mapped_Type",
                "query_used",
                "sentiment",
            ]
        )

    raw_df = pd.DataFrame(all_rows)

    # Drop empty core fields and normalize text before dedup.
    raw_df["title"] = raw_df["title"].fillna("").astype(str).str.strip()
    raw_df["summary"] = raw_df["summary"].fillna("").astype(str).str.strip()
    raw_df["link"] = raw_df["link"].fillna("").astype(str).str.strip()
    raw_df = raw_df[(raw_df["title"] != "") & (raw_df["link"] != "")]

    # Deduplicate by link first, then title fallback.
    raw_df = raw_df.drop_duplicates(subset=["link"])
    raw_df = raw_df.drop_duplicates(subset=["title"])

    # Convert and filter to the required lookback window (last 1 month by default).
    raw_df["published_dt"] = pd.to_datetime(raw_df["published"], errors="coerce", utc=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    raw_df = raw_df[raw_df["published_dt"].notna() & (raw_df["published_dt"] >= cutoff)]

    # Company mapping from combined text with company-wise query preference.
    combined_text = (raw_df["title"] + " " + raw_df["summary"]).str.lower()
    mapped = [
        map_company(text, preferred_ticker=ticker)
        for text, ticker in zip(combined_text, raw_df["target_ticker"])
    ]
    raw_df[["Ticker", "Company", "Mapped_Type"]] = pd.DataFrame(
        mapped, index=raw_df.index
    )

    # Company-wise fallback: keep fetched rows tied to their intended company bucket.
    missing_map = raw_df["Ticker"].isna()
    raw_df.loc[missing_map, "Ticker"] = raw_df.loc[missing_map, "target_ticker"]
    raw_df.loc[missing_map, "Company"] = raw_df.loc[missing_map, "target_company"]
    raw_df.loc[missing_map, "Mapped_Type"] = raw_df.loc[missing_map, "query_type"].map(
        {"Company": "Direct", "Domain": "Domain"}
    )

    if not keep_unmapped:
        raw_df = raw_df[raw_df["Ticker"].notna()]

    # Standardize date format.
    raw_df["Date"] = raw_df["published_dt"]
    raw_df["Date"] = raw_df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    # Final structure for sentiment pipeline.
    final_df = raw_df.rename(
        columns={
            "title": "Title",
            "summary": "Summary",
            "link": "Link",
        }
    )[
        [
            "Date",
            "Ticker",
            "Company",
            "Title",
            "Summary",
            "Link",
            "Mapped_Type",
            "query_used",
        ]
    ].copy()
    final_df.insert(3, "Source", SOURCE_NAME)
    final_df["sentiment"] = "PENDING"

    # Final clean pass.
    final_df = final_df.dropna(subset=["Date", "Ticker", "Company", "Title", "Link"])
    final_df = final_df.drop_duplicates(subset=["Link", "Title"])
    final_df = final_df.sort_values("Date", ascending=False).reset_index(drop=True)

    return final_df


def save_outputs(df: pd.DataFrame) -> None:
    """Save raw/processed CSVs and an Excel master file."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "rss_news.csv"
    cleaned_path = processed_dir / "rss_cleaned.csv"
    excel_path = Path("master_rss_dataset.xlsx")

    # Keep same schema for raw/clean in this hackathon pipeline.
    df.to_csv(raw_path, index=False, encoding="utf-8")
    df.to_csv(cleaned_path, index=False, encoding="utf-8")

    try:
        df.to_excel(excel_path, index=False)
    except Exception as exc:  # pragma: no cover - depends on openpyxl availability
        print(f"[WARN] Could not write Excel file ({excel_path}): {exc}")

    print(f"[OK] Saved CSV (raw): {raw_path}")
    print(f"[OK] Saved CSV (cleaned): {cleaned_path}")
    print(f"[OK] Saved Excel: {excel_path}")


def main() -> None:
    print("[INFO] Building RSS dataset...")
    df = build_dataset(
        max_results_per_query=DEFAULT_MAX_RESULTS_PER_QUERY,
        keep_unmapped=False,
        lookback_days=DEFAULT_LOOKBACK_DAYS,
        window_days=DEFAULT_WINDOW_DAYS,
    )
    print(f"[INFO] Final dataset rows: {len(df)}")
    save_outputs(df)
    print("[INFO] Pipeline completed.")


if __name__ == "__main__":
    main()
