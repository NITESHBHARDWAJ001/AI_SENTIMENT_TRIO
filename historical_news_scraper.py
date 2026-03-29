"""
Historical News Archival & Analysis Pipeline (1 Year)

What this script does:
- Scrapes 1 year of news for all 15 companies using Google News RSS
- Uses extended lookback + multiple query variations
- Stores complete news archive with metadata
- Analyzes news volume and patterns
- Prepares data for robust sentiment analysis
- Generates decision-making statistics

Run:
    python historical_news_scraper.py
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus

import feedparser
import pandas as pd

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


TICKERS: List[str] = [
    "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN",
    "NVDA", "META", "JPM", "XOM", "WMT",
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "ICICIBANK.NS",
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
    "TSLA": ["ev", "electric vehicle", "battery", "elon musk", "tesla"],
    "AAPL": ["iphone", "ios", "apple", "mac"],
    "MSFT": ["cloud", "azure", "microsoft", "windows"],
    "GOOGL": ["search", "ads", "google", "alphabet"],
    "AMZN": ["ecommerce", "aws", "amazon"],
    "NVDA": ["ai", "gpu", "chips", "nvidia"],
    "META": ["social media", "ads", "facebook"],
    "JPM": ["bank", "interest rate", "jpmorgan"],
    "XOM": ["oil", "crude", "energy", "exxon"],
    "WMT": ["retail", "consumer", "walmart"],
    "TCS.NS": ["it", "software", "outsourcing", "tcs"],
    "INFY.NS": ["it", "consulting", "infosys"],
    "HDFCBANK.NS": ["banking", "loan", "hdfc"],
    "ICICIBANK.NS": ["banking", "finance", "icici"],
}

BASE_RSS_URL = "https://news.google.com/rss/search?q={}"
ARCHIVE_DIR = Path("data/archive")
ARCHIVE_CSV = ARCHIVE_DIR / "news_archive_1year.csv"
STATS_FILE = ARCHIVE_DIR / "archive_statistics.txt"


def _normalize_spaces(text: str) -> str:
    """Normalize whitespace in text."""
    return re.sub(r"\s+", " ", text or "").strip()


def _contains_term(text: str, term: str) -> bool:
    """Match whole terms where possible."""
    term = re.escape(term.lower().strip())
    if not term:
        return False
    pattern = rf"\b{term}\b"
    return re.search(pattern, text.lower()) is not None


def generate_query_variants(ticker: str, company: str) -> List[Tuple[str, str]]:
    """
    Generate multiple query variations for better coverage.
    
    Returns list of (query, query_type) tuples.
    """
    queries: List[Tuple[str, str]] = []
    
    # Company queries
    queries.append((f"{company} stock", "company_stock"))
    queries.append((f"{company} share price", "company_price"))
    queries.append((f"{company} earnings", "company_earnings"))
    queries.append((f"{company} news", "company_news"))
    queries.append((f"{ticker} stock", "ticker_stock"))
    
    # Domain queries
    for keyword in DOMAIN_MAP.get(ticker, []):
        queries.append((f"{keyword} price", "domain_price"))
        queries.append((f"{keyword} news", "domain_news"))
        queries.append((f"{keyword} market", "domain_market"))
    
    return queries


def fetch_rss_news_extended(
    query: str,
    lookback_days: int = 365,
    max_results: int = 100,
) -> List[Dict[str, str]]:
    """
    Fetch news from Google News RSS with extended lookback.
    
    Note: Google News RSS doesn't strictly support historical queries,
    but the API will return whatever recent news matches the query.
    """
    rss_url = BASE_RSS_URL.format(quote_plus(query))
    feed = feedparser.parse(rss_url)
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    rows: List[Dict[str, str]] = []
    
    for entry in feed.entries[:max_results]:
        try:
            pub_date = pd.to_datetime(entry.get("published", ""), utc=True, errors="coerce")
            
            # Accept all dates (don't filter by lookback here; filter during processing)
            if pd.isna(pub_date):
                continue
            
            rows.append({
                "title": _normalize_spaces(entry.get("title", "")),
                "summary": _normalize_spaces(entry.get("summary", "")),
                "published": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "published_date": pub_date.strftime("%Y-%m-%d"),
                "link": _normalize_spaces(entry.get("link", "")),
                "source": entry.get("source", {}).get("title", "Google News") if isinstance(entry.get("source"), dict) else "Google News",
                "query": query,
                "query_type": "rss",
            })
        except Exception:
            continue
    
    return rows


def scrape_company_news(
    ticker: str,
    company: str,
    lookback_days: int = 365,
) -> List[Dict[str, str]]:
    """Scrape news for one company using query variants."""
    all_articles: List[Dict[str, str]] = []
    queries = generate_query_variants(ticker, company)
    
    print(f"[INFO] Scraping {ticker} ({company}) with {len(queries)} query variants...")
    
    for query, query_type in queries:
        try:
            articles = fetch_rss_news_extended(query, lookback_days=lookback_days, max_results=50)
            for article in articles:
                article["ticker"] = ticker
                article["company_name"] = company
                article["query_type"] = query_type
                all_articles.append(article)
            
            print(f"  ✓ {query_type}: {len(articles)} articles")
        except Exception as e:
            print(f"  ✗ {query_type} failed: {str(e)}")
    
    return all_articles


def deduplicate_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate articles by link and title."""
    seen_links: Set[str] = set()
    seen_titles: Set[str] = set()
    deduplicated: List[Dict[str, str]] = []
    
    for article in articles:
        link = article.get("link", "").strip()
        title = article.get("title", "").strip()
        
        if link and link in seen_links:
            continue
        if title and title in seen_titles:
            continue
        
        if link:
            seen_links.add(link)
        if title:
            seen_titles.add(title)
        
        deduplicated.append(article)
    
    return deduplicated


def build_news_archive(
    tickers: Optional[List[str]] = None,
    lookback_days: int = 365,
) -> pd.DataFrame:
    """Build complete 1-year news archive for all companies."""
    tickers = tickers or TICKERS
    all_articles: List[Dict[str, str]] = []
    
    iterator = tqdm(tickers, desc="News archival", unit="ticker") if tqdm else tickers
    
    for ticker in iterator:
        company = COMPANY_MAP[ticker]
        articles = scrape_company_news(ticker, company, lookback_days=lookback_days)
        all_articles.extend(articles)
    
    if not all_articles:
        print("[WARN] No articles found.")
        return pd.DataFrame()
    
    print(f"\n[INFO] Total articles before dedup: {len(all_articles):,}")
    
    # Convert to dataframe
    df = pd.DataFrame(all_articles)
    
    # Normalize columns
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["summary"] = df["summary"].fillna("").astype(str).str.strip()
    df["link"] = df["link"].fillna("").astype(str).str.strip()
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    
    # Drop empty entries
    df = df[(df["title"] != "") & (df["link"] != "")]
    
    # Deduplicate
    all_articles_deduplicated = df.to_dict(orient="records")
    unique_articles = deduplicate_articles(all_articles_deduplicated)
    df = pd.DataFrame(unique_articles)
    
    print(f"[INFO] Total articles after dedup: {len(df):,}")
    
    # Filter to lookback window (use tz-naive cutoff to match published_date)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=lookback_days)
    df = df[df["published_date"] >= cutoff]
    
    print(f"[INFO] Articles within {lookback_days} days: {len(df):,}")
    
    # Sort by date
    df = df.sort_values("published_date", ascending=False).reset_index(drop=True)
    
    return df[["published_date", "ticker", "company_name", "title", "summary", "link", "source", "query_type"]].copy()


def save_archive(df: pd.DataFrame) -> None:
    """Save news archive to CSV."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(ARCHIVE_CSV, index=False, encoding="utf-8")
    print(f"\n[OK] Saved archive: {ARCHIVE_CSV}")


def generate_archive_statistics(df: pd.DataFrame) -> str:
    """Generate statistics about the news archive."""
    stats_lines: List[str] = []
    
    stats_lines.append("=" * 80)
    stats_lines.append("NEWS ARCHIVE STATISTICS (1 YEAR)")
    stats_lines.append("=" * 80)
    stats_lines.append("")
    
    stats_lines.append("OVERALL SUMMARY")
    stats_lines.append("-" * 80)
    stats_lines.append(f"Total unique articles:                {len(df):,}")
    stats_lines.append(f"Date range:                          {df['published_date'].min().date()} to {df['published_date'].max().date()}")
    stats_lines.append(f"Number of tickers:                   {df['ticker'].nunique()}")
    stats_lines.append(f"Number of sources:                   {df['source'].nunique()}")
    stats_lines.append("")
    
    # Per-ticker breakdown
    stats_lines.append("ARTICLES PER TICKER")
    stats_lines.append("-" * 80)
    ticker_counts = df["ticker"].value_counts().sort_values(ascending=False)
    for ticker, count in ticker_counts.items():
        company = COMPANY_MAP.get(ticker, ticker)
        coverage_pct = 100 * count / len(df) if len(df) > 0 else 0
        stats_lines.append(f"{ticker:<20} {count:>8} articles ({coverage_pct:>5.1f}%)")
    
    stats_lines.append("")
    
    # Per-query-type breakdown
    stats_lines.append("ARTICLES BY QUERY TYPE")
    stats_lines.append("-" * 80)
    query_counts = df["query_type"].value_counts().sort_values(ascending=False)
    for query_type, count in query_counts.items():
        coverage_pct = 100 * count / len(df) if len(df) > 0 else 0
        stats_lines.append(f"{query_type:<30} {count:>8} articles ({coverage_pct:>5.1f}%)")
    
    stats_lines.append("")
    
    # Temporal distribution
    stats_lines.append("TEMPORAL DISTRIBUTION")
    stats_lines.append("-" * 80)
    df_copy = df.copy()
    df_copy["month"] = df_copy["published_date"].dt.to_period("M")
    monthly_counts = df_copy["month"].value_counts().sort_index(ascending=False)
    for month, count in monthly_counts.head(12).items():
        stats_lines.append(f"{str(month):<20} {count:>8} articles")
    
    stats_lines.append("")
    
    # Quality checks
    stats_lines.append("DATA QUALITY CHECKS")
    stats_lines.append("-" * 80)
    
    empty_summaries = (df["summary"] == "").sum()
    stats_lines.append(f"Articles with empty summary:         {empty_summaries:>8} ({100*empty_summaries/len(df):.1f}%)")
    
    duplicate_titles = len(df) - df["title"].nunique()
    stats_lines.append(f"Potential duplicate titles:          {duplicate_titles:>8} ({100*duplicate_titles/len(df):.1f}%)")
    
    min_per_ticker = ticker_counts.min()
    max_per_ticker = ticker_counts.max()
    avg_per_ticker = ticker_counts.mean()
    stats_lines.append(f"Min articles per ticker:             {int(min_per_ticker):>8}")
    stats_lines.append(f"Max articles per ticker:             {int(max_per_ticker):>8}")
    stats_lines.append(f"Avg articles per ticker:             {avg_per_ticker:>8.1f}")
    
    stats_lines.append("")
    stats_lines.append("DECISION-MAKING READINESS")
    stats_lines.append("-" * 80)
    
    if avg_per_ticker >= 50:
        stats_lines.append("✓ EXCELLENT: Sufficient data for robust sentiment analysis")
    elif avg_per_ticker >= 30:
        stats_lines.append("✓ GOOD: Adequate data for sentiment analysis")
    elif avg_per_ticker >= 10:
        stats_lines.append("⚠ FAIR: Limited data, use with caution")
    else:
        stats_lines.append("✗ INSUFFICIENT: Not enough data for reliable decisions")
    
    if min_per_ticker >= avg_per_ticker * 0.5:
        stats_lines.append("✓ BALANCED: Good coverage across all tickers")
    else:
        stats_lines.append(f"⚠ IMBALANCED: Some tickers have much less data (min={int(min_per_ticker)}, avg={avg_per_ticker:.1f})")
    
    stats_lines.append("")
    stats_lines.append("=" * 80)
    
    return "\n".join(stats_lines)


def main() -> None:
    print("[INFO] Building 1-year historical news archive...\n")
    
    # Build archive
    archive_df = build_news_archive(tickers=TICKERS, lookback_days=365)
    
    if archive_df.empty:
        print("[ERROR] No articles found for any ticker.")
        return
    
    # Save archive
    save_archive(archive_df)
    
    # Generate and save statistics
    stats = generate_archive_statistics(archive_df)
    print("\n" + stats)
    
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        f.write(stats)
    print(f"\n[OK] Statistics saved to: {STATS_FILE}")


if __name__ == "__main__":
    main()
