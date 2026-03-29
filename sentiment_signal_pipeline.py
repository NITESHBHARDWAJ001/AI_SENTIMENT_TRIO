"""
Sentiment + Signal generation pipeline for AI Stock Market Analyzer.

What this script does:
- Fetches recent news (last 14 days) using Google News RSS
- Maps articles to companies (direct + domain matching)
- Performs sentiment analysis (FinBERT with VADER fallback)
- Aggregates sentiment daily by ticker
- Loads existing stock data from data/raw/{ticker}_stock.csv
- Merges sentiment + stock features
- Generates BUY/SELL/HOLD signals with confidence scores
- Saves per-ticker and master final datasets

Run:
    python sentiment_signal_pipeline.py
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import feedparser
import numpy as np
import pandas as pd

try:
    from transformers import pipeline as hf_pipeline
    HAS_FINBERT = True
except ImportError:
    HAS_FINBERT = False

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk
    try:
        nltk.data.find('sentiment/vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    HAS_VADER = True
except ImportError:
    HAS_VADER = False

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

BASE_RSS_URL = "https://news.google.com/rss/search?q={}"
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Signal thresholds
BUY_THRESHOLD = 0.2
SELL_THRESHOLD = -0.2


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


def fetch_rss_news(
    query: str,
    lookback_days: int = 14,
    max_results: int = 25,
) -> List[Dict[str, str]]:
    """Fetch recent news from Google News RSS."""
    rss_url = BASE_RSS_URL.format(quote_plus(query))
    feed = feedparser.parse(rss_url)
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    rows: List[Dict[str, str]] = []
    
    for entry in feed.entries[:max_results]:
        try:
            pub_date = pd.to_datetime(entry.get("published", ""), utc=True, errors="coerce")
            if pd.isna(pub_date) or pub_date < cutoff:
                continue
            
            rows.append({
                "title": _normalize_spaces(entry.get("title", "")),
                "summary": _normalize_spaces(entry.get("summary", "")),
                "published": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "link": _normalize_spaces(entry.get("link", "")),
                "query_used": query,
            })
        except Exception:
            continue
    
    return rows


def clean_news(rows: List[Dict[str, str]]) -> pd.DataFrame:
    """Clean and deduplicate news data."""
    if not rows:
        return pd.DataFrame(columns=["date", "title", "summary", "link", "query_used"])
    
    df = pd.DataFrame(rows)
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["summary"] = df["summary"].fillna("").astype(str).str.strip()
    df["link"] = df["link"].fillna("").astype(str).str.strip()
    
    # Drop empty entries
    df = df[(df["title"] != "") & (df["link"] != "")]
    
    # Deduplicate
    df = df.drop_duplicates(subset=["link"])
    df = df.drop_duplicates(subset=["title"])
    
    # Standardize date
    df["published"] = pd.to_datetime(df["published"], errors="coerce")
    df["date"] = df["published"].dt.strftime("%Y-%m-%d")
    
    return df[["date", "title", "summary", "link", "query_used"]].reset_index(drop=True)


def map_company(text: str, preferred_ticker: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Map text to ticker with priority: preferred -> direct -> domain."""
    text_l = (text or "").lower()
    
    # Preferred ticker first
    if preferred_ticker and preferred_ticker in COMPANY_MAP:
        company = COMPANY_MAP[preferred_ticker]
        if _contains_term(text_l, company.lower()) or _contains_term(text_l, preferred_ticker.lower()):
            return preferred_ticker, "direct"
        
        for kw in DOMAIN_MAP.get(preferred_ticker, []):
            if _contains_term(text_l, kw.lower()):
                return preferred_ticker, "domain"
    
    # Global direct match
    for ticker, company in COMPANY_MAP.items():
        if _contains_term(text_l, company.lower()) or _contains_term(text_l, ticker.lower()):
            return ticker, "direct"
    
    # Global domain match
    for ticker, keywords in DOMAIN_MAP.items():
        for kw in keywords:
            if _contains_term(text_l, kw.lower()):
                return ticker, "domain"
    
    return None, "none"


def compute_sentiment(text: str) -> float:
    """Compute sentiment score in range [-1, +1]."""
    if not text or not text.strip():
        return 0.0
    
    # Try FinBERT if available
    if HAS_FINBERT:
        try:
            classifier = hf_pipeline("sentiment-analysis", model="ProsusAI/finbert")
            result = classifier(text[:512])  # Truncate to 512 chars for efficiency
            label = result[0]["label"].lower()
            score = result[0]["score"]
            
            if "positive" in label:
                return float(score)
            elif "negative" in label:
                return -float(score)
            else:  # neutral
                return 0.0
        except Exception:
            pass
    
    # Fallback to VADER
    if HAS_VADER:
        try:
            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(text)
            return float(scores["compound"])  # [-1, +1]
        except Exception:
            pass
    
    # Fallback: simple keyword scoring
    positive_words = {"gain", "bull", "rise", "surge", "profit", "good", "strong", "beat"}
    negative_words = {"loss", "bear", "fall", "drop", "weak", "miss", "risk"}
    
    text_l = text.lower()
    pos_count = sum(1 for w in positive_words if _contains_term(text_l, w))
    neg_count = sum(1 for w in negative_words if _contains_term(text_l, w))
    total = pos_count + neg_count
    
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total


def aggregate_sentiment_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sentiment by ticker and date."""
    if df.empty:
        return pd.DataFrame(columns=["ticker", "date", "sentiment", "article_count"])
    
    agg = df.groupby(["ticker", "date"]).agg({
        "sentiment": ["mean", "count"]
    }).reset_index()
    
    agg.columns = ["ticker", "date", "sentiment", "article_count"]
    agg["sentiment"] = agg["sentiment"].round(4)
    
    return agg.sort_values(["ticker", "date"]).reset_index(drop=True)


def load_stock_data(ticker: str) -> pd.DataFrame:
    """Load existing stock CSV data."""
    stock_path = RAW_DATA_DIR / f"{ticker}_stock.csv"
    
    if not stock_path.exists():
        print(f"[WARN] Stock data missing for {ticker}: {stock_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(stock_path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    
    required = ["Date", "Close", "Volume"]
    if not all(col in df.columns for col in required):
        print(f"[WARN] Missing required columns in {ticker} stock data")
        return pd.DataFrame()
    
    return df[required].drop_duplicates(subset=["Date"]).reset_index(drop=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical features to stock data."""
    if df.empty:
        return df
    
    out = df.copy()
    out = out.sort_values("Date").reset_index(drop=True)
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    out = out.dropna(subset=["Close"])
    
    out["return_1d"] = out["Close"].pct_change()
    out["return_5d"] = out["Close"].pct_change(periods=5)
    out["momentum"] = out["Close"] - out["Close"].shift(5)
    out["volatility"] = out["return_1d"].rolling(window=5, min_periods=5).std()
    
    return out


def merge_data(stock_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """Merge stock + sentiment data."""
    if stock_df.empty:
        return pd.DataFrame()
    
    merged = stock_df.copy()
    merged["date"] = merged["Date"]
    
    # Create a result dataframe with all stock dates
    result = merged[["date", "Close", "return_1d", "momentum", "volatility"]].copy()
    result["sentiment"] = 0.0
    result["article_count"] = 0
    result["sentiment_source"] = "default"  # Track if real sentiment or default
    
    if not sentiment_df.empty:
        sent_daily = sentiment_df.copy()
        sent_daily["sentiment"] = pd.to_numeric(sent_daily["sentiment"], errors="coerce").fillna(0.0)
        sent_daily["article_count"] = pd.to_numeric(sent_daily["article_count"], errors="coerce").fillna(0).astype(int)
        
        # Merge on date - left join keeps all stock dates
        merged_temp = result.merge(
            sent_daily[["date", "sentiment", "article_count"]],
            on="date",
            how="left",
            suffixes=("", "_news")
        )
        
        # For dates with news, use those values; otherwise use defaults
        has_news = merged_temp["article_count"].notna() & (merged_temp["article_count"] > 0)
        result.loc[has_news, "sentiment"] = merged_temp.loc[has_news, "sentiment_news"].fillna(0.0)
        result.loc[has_news, "article_count"] = merged_temp.loc[has_news, "article_count"].fillna(0).astype(int)
        result.loc[has_news, "sentiment_source"] = "news"
    
    return result[["date", "Close", "return_1d", "momentum", "volatility", "sentiment", "article_count", "sentiment_source"]]


def compute_signal(
    sentiment: float,
    return_1d: float,
    momentum: float,
    volatility: float,
) -> Tuple[str, float, float]:
    """
    Compute signal and confidence.
    
    Returns: (signal, score, confidence)
    """
    # Handle NaNs
    sentiment = 0.0 if pd.isna(sentiment) else float(sentiment)
    return_1d = 0.0 if pd.isna(return_1d) else float(return_1d)
    momentum = 0.0 if pd.isna(momentum) else float(momentum)
    volatility = 0.0 if pd.isna(volatility) else float(volatility)
    
    # Weighted score
    score = 0.6 * sentiment + 0.25 * return_1d + 0.15 * momentum
    
    # Signal thresholds
    if score > BUY_THRESHOLD:
        signal = "BUY"
    elif score < SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    # Confidence: based on sentiment strength and inverse volatility
    confidence = abs(sentiment) * max(0, 1.0 - volatility) if not pd.isna(volatility) else abs(sentiment)
    confidence = min(1.0, max(0.0, confidence))
    
    return signal, score, confidence


def generate_final_dataset(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    """Run end-to-end pipeline: news → sentiment → merge → signal."""
    tickers = tickers or TICKERS
    all_frames: List[pd.DataFrame] = []
    
    print("[INFO] Starting sentiment + signal pipeline...")
    iterator = tqdm(tickers, desc="Ticker pipeline", unit="ticker") if tqdm else tickers
    
    for ticker in iterator:
        print(f"\n[INFO] Processing {ticker}...")
        
        # Fetch news for company query
        company = COMPANY_MAP[ticker]
        company_query = f"{company} stock OR shares OR earnings"
        news_rows = fetch_rss_news(company_query, lookback_days=14, max_results=25)
        
        # Fetch news for domain queries
        for keyword in DOMAIN_MAP.get(ticker, []):
            domain_query = f"{keyword} market OR industry"
            news_rows.extend(fetch_rss_news(domain_query, lookback_days=14, max_results=25))
        
        if not news_rows:
            print(f"[WARN] No news found for {ticker}")
            continue
        
        # Clean and map
        news_df = clean_news(news_rows)
        combined_text = (news_df["title"] + " " + news_df["summary"]).str.lower()
        mapped = [map_company(text, preferred_ticker=ticker) for text in combined_text]
        news_df[["mapped_ticker", "mapping_type"]] = pd.DataFrame(
            mapped, index=news_df.index
        )
        
        # Keep only rows mapped to this ticker
        news_df = news_df[news_df["mapped_ticker"] == ticker].copy()
        if news_df.empty:
            print(f"[WARN] No articles mapped to {ticker}")
            continue
        
        # Sentiment analysis - compute for each article
        print(f"[DEBUG] Computing sentiment for {len(news_df)} articles...")
        sentiment_scores = []
        for idx, row in news_df.iterrows():
            combined_text = f"{row.get('title', '')} {row.get('summary', '')}"
            score = compute_sentiment(combined_text)
            sentiment_scores.append(score)
        
        news_df["sentiment"] = sentiment_scores
        news_df["sentiment"] = pd.to_numeric(news_df["sentiment"], errors="coerce").fillna(0.0)
        
        # Debug: show sample sentiments
        if len(news_df) > 0:
            print(f"[DEBUG] Sample sentiments (first 5): {news_df['sentiment'].head().tolist()}")
            print(f"[DEBUG] Sentiment stats: mean={news_df['sentiment'].mean():.4f}, min={news_df['sentiment'].min():.4f}, max={news_df['sentiment'].max():.4f}")
        
        # Daily aggregation
        agg_input = news_df[["date", "sentiment"]].assign(ticker=ticker).copy()
        print(f"[DEBUG] Before aggregation - rows: {len(agg_input)}, unique dates: {agg_input['date'].nunique()}")
        
        sentiment_daily = aggregate_sentiment_daily(agg_input)
        print(f"[DEBUG] After aggregation - rows: {len(sentiment_daily)}")
        print(f"[DEBUG] Aggregated sentiment sample: {sentiment_daily[['date', 'sentiment', 'article_count']].head().values.tolist()}")
        
        # Load stock data
        stock_df = load_stock_data(ticker)
        if stock_df.empty:
            print(f"[WARN] Skipping {ticker}: no stock data")
            continue
        
        # Add features
        stock_df = add_features(stock_df)
        
        # Merge
        merged_df = merge_data(stock_df, sentiment_daily)
        if merged_df.empty:
            print(f"[WARN] Merged data empty for {ticker}")
            continue
        
        # Generate signals
        signals_list = [
            compute_signal(row["sentiment"], row["return_1d"], row["momentum"], row["volatility"])
            for _, row in merged_df.iterrows()
        ]
        merged_df[["signal", "score", "confidence"]] = pd.DataFrame(
            signals_list, index=merged_df.index
        )
        
        # Add metadata
        merged_df["ticker"] = ticker
        merged_df["company_name"] = company
        
        # Reorder columns
        final_cols = [
            "date", "ticker", "company_name", "Close",
            "sentiment", "sentiment_source", "return_1d", "momentum", "volatility",
            "score", "signal", "confidence", "article_count"
        ]
        merged_df = merged_df[[c for c in final_cols if c in merged_df.columns]]
        
        # Save per-ticker
        ticker_path = PROCESSED_DIR / f"{ticker}_final.csv"
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(ticker_path, index=False, encoding="utf-8")
        
        # Show sentiment coverage stats
        if "sentiment_source" in merged_df.columns:
            real_sentiment = (merged_df["sentiment_source"] == "news").sum()
            total = len(merged_df)
            coverage = 100 * real_sentiment / total if total > 0 else 0
            mean_sentiment = merged_df["sentiment"].mean()
            print(f"[OK] Saved {ticker}: {ticker_path} | Coverage: {real_sentiment}/{total} dates ({coverage:.1f}%) | Mean sentiment: {mean_sentiment:.4f}")
        else:
            print(f"[OK] Saved {ticker}: {ticker_path}")
        
        all_frames.append(merged_df)
    
    if not all_frames:
        print("[WARN] No final datasets were built.")
        return pd.DataFrame()
    
    master_df = pd.concat(all_frames, ignore_index=True)
    master_df = master_df.sort_values(["ticker", "date"]).reset_index(drop=True)
    
    # Save master
    master_csv = Path("master_sentiment_dataset.csv")
    master_df.to_csv(master_csv, index=False, encoding="utf-8")
    print(f"[OK] Saved master CSV: {master_csv}")
    
    try:
        master_xlsx = Path("master_sentiment_dataset.xlsx")
        master_df.to_excel(master_xlsx, index=False)
        print(f"[OK] Saved master Excel: {master_xlsx}")
    except Exception as e:
        print(f"[WARN] Could not save Excel: {e}")
    
    return master_df


def main() -> None:
    print("[INFO] AI Stock Market Sentiment Analyzer")
    print("[INFO] Loading stock data + fetching news + computing sentiment...\n")
    
    final_df = generate_final_dataset(tickers=TICKERS)
    print(f"\n[INFO] Final dataset rows: {len(final_df)}")
    print("[INFO] Pipeline completed.")


if __name__ == "__main__":
    main()
