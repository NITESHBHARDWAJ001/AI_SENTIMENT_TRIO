"""
Enhanced Sentiment Analysis using Historical News Archive

What this script does:
- Loads the 1-year news archive (from historical_news_scraper.py)
- Computes sentiment for ALL historical articles
- Generates daily, weekly, and monthly sentiment aggregations
- Merges with stock data
- Produces BUY/SELL/HOLD signals with higher confidence
- Generates trend analysis and decision reports

Run:
    python sentiment_from_archive.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

ARCHIVE_CSV = Path("data/archive/news_archive_1year.csv")
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("data/reports")

BUY_THRESHOLD = 0.2
SELL_THRESHOLD = -0.2


def compute_sentiment(text: str) -> float:
    """Compute sentiment score in range [-1, +1]."""
    if not text or not text.strip():
        return 0.0
    
    # Try FinBERT if available
    if HAS_FINBERT:
        try:
            classifier = hf_pipeline("sentiment-analysis", model="ProsusAI/finbert")
            result = classifier(text[:512])
            label = result[0]["label"].lower()
            score = result[0]["score"]
            
            if "positive" in label:
                return float(score)
            elif "negative" in label:
                return -float(score)
            else:
                return 0.0
        except Exception:
            pass
    
    # Fallback to VADER
    if HAS_VADER:
        try:
            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(text)
            return float(scores["compound"])
        except Exception:
            pass
    
    # Fallback: simple keyword scoring
    positive_words = {"gain", "bull", "rise", "surge", "profit", "good", "strong", "beat", "upbeat", "optimistic"}
    negative_words = {"loss", "bear", "fall", "drop", "weak", "miss", "risk", "decline", "pessimistic"}
    
    text_l = text.lower()
    pos_count = sum(1 for w in positive_words if re.search(rf"\b{w}\b", text_l))
    neg_count = sum(1 for w in negative_words if re.search(rf"\b{w}\b", text_l))
    total = pos_count + neg_count
    
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total


def load_news_archive() -> pd.DataFrame:
    """Load the 1-year news archive."""
    if not ARCHIVE_CSV.exists():
        print(f"[ERROR] Archive not found: {ARCHIVE_CSV}")
        print("[INFO] Run: python historical_news_scraper.py")
        return pd.DataFrame()
    
    df = pd.read_csv(ARCHIVE_CSV)
    df["published_date"] = pd.to_datetime(df["published_date"])
    print(f"[OK] Loaded {len(df):,} articles from archive")
    return df


def compute_sentiment_archive(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sentiment for all articles in archive."""
    print("[INFO] Computing sentiment for historical articles...")
    
    sentiments: List[float] = []
    iterator = df.iterrows()
    
    if tqdm:
        iterator = tqdm(iterator, total=len(df), desc="Sentiment analysis")
    
    for _, row in iterator:
        combined_text = f"{row.get('title', '')} {row.get('summary', '')}"
        sentiment = compute_sentiment(combined_text)
        sentiments.append(sentiment)
    
    df["sentiment"] = sentiments
    print(f"[OK] Sentiment range: [{df['sentiment'].min():.4f}, {df['sentiment'].max():.4f}]")
    print(f"[OK] Mean sentiment: {df['sentiment'].mean():.4f}")
    
    return df


def aggregate_sentiment_daily(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Aggregate sentiment by date for one ticker."""
    ticker_df = df[df["ticker"] == ticker].copy()
    
    agg = ticker_df.groupby("published_date").agg({
        "sentiment": ["mean", "std", "min", "max", "count"],
        "title": lambda x: list(x)[:3],  # Top 3 headlines
    }).reset_index()
    
    agg.columns = ["date", "sentiment", "sentiment_std", "sentiment_min", "sentiment_max", "article_count", "headlines"]
    agg["date"] = agg["date"].dt.strftime("%Y-%m-%d")
    agg["sentiment"] = agg["sentiment"].round(4)
    agg["sentiment_std"] = agg["sentiment_std"].fillna(0).round(4)
    
    return agg.sort_values("date").reset_index(drop=True)


def load_stock_data(ticker: str) -> pd.DataFrame:
    """Load stock data for one ticker."""
    stock_path = RAW_DATA_DIR / f"{ticker}_stock.csv"
    
    if not stock_path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(stock_path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    
    required = ["Date", "Close", "Volume"]
    if not all(col in df.columns for col in required):
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


def merge_sentiment_stock(sentiment_df: pd.DataFrame, stock_df: pd.DataFrame) -> pd.DataFrame:
    """Merge sentiment and stock data."""
    if stock_df.empty or sentiment_df.empty:
        return pd.DataFrame()
    
    merged = stock_df.copy()
    merged["date"] = merged["Date"].str.replace("-", "-")
    
    result = merged.merge(
        sentiment_df,
        left_on="date",
        right_on="date",
        how="left"
    )
    
    result["sentiment"] = result["sentiment"].fillna(0.0).astype(float)
    result["article_count"] = result["article_count"].fillna(0).astype(int)
    result["sentiment_std"] = result["sentiment_std"].fillna(0).astype(float)
    
    return result


def compute_signal(
    sentiment: float,
    return_1d: float,
    momentum: float,
    volatility: float,
    article_count: int = 0,
) -> Tuple[str, float, float]:
    """Compute signal with article count weighting."""
    sentiment = 0.0 if pd.isna(sentiment) else float(sentiment)
    return_1d = 0.0 if pd.isna(return_1d) else float(return_1d)
    momentum = 0.0 if pd.isna(momentum) else float(momentum)
    volatility = 0.0 if pd.isna(volatility) else float(volatility)
    article_count = int(article_count) if not pd.isna(article_count) else 0
    
    # Weight sentiment by article count (more articles = more confidence)
    sentiment_weight = min(1.0, article_count / 10.0) if article_count > 0 else 0.0
    weighted_sentiment = sentiment * sentiment_weight
    
    # Weighted score
    score = 0.6 * weighted_sentiment + 0.25 * return_1d + 0.15 * momentum
    
    # Signal thresholds
    if score > BUY_THRESHOLD:
        signal = "BUY"
    elif score < SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    # Confidence
    confidence = abs(weighted_sentiment) * max(0, 1.0 - volatility) if not pd.isna(volatility) else abs(weighted_sentiment)
    confidence = min(1.0, max(0.0, confidence))
    
    return signal, score, confidence


def generate_final_datasets(sentiment_archive: pd.DataFrame) -> pd.DataFrame:
    """Generate final decision datasets for all tickers."""
    all_frames: List[pd.DataFrame] = []
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    iterator = tqdm(TICKERS, desc="Final datasets", unit="ticker") if tqdm else TICKERS
    
    for ticker in iterator:
        print(f"\n[INFO] Processing {ticker}...")
        company = COMPANY_MAP[ticker]
        
        # Aggregate sentiment daily
        sentiment_daily = aggregate_sentiment_daily(sentiment_archive, ticker)
        if sentiment_daily.empty:
            print(f"[WARN] No sentiment data for {ticker}")
            continue
        
        # Load stock data
        stock_df = load_stock_data(ticker)
        if stock_df.empty:
            print(f"[WARN] No stock data for {ticker}")
            continue
        
        # Add features
        stock_df = add_features(stock_df)
        
        # Merge
        merged_df = merge_sentiment_stock(sentiment_daily, stock_df)
        if merged_df.empty:
            print(f"[WARN] Merged data empty for {ticker}")
            continue
        
        # Generate signals
        signals_list = [
            compute_signal(row["sentiment"], row["return_1d"], row["momentum"], row["volatility"], row["article_count"])
            for _, row in merged_df.iterrows()
        ]
        merged_df[["signal", "score", "confidence"]] = pd.DataFrame(signals_list, index=merged_df.index)
        
        # Add metadata
        merged_df["ticker"] = ticker
        merged_df["company_name"] = company
        
        # Select columns
        final_cols = [
            "date", "ticker", "company_name", "Close",
            "sentiment", "sentiment_std", "return_1d", "momentum", "volatility",
            "score", "signal", "confidence", "article_count"
        ]
        merged_df = merged_df[[c for c in final_cols if c in merged_df.columns]]
        
        # Save per-ticker
        ticker_path = PROCESSED_DIR / f"{ticker}_sentiment_archive.csv"
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(ticker_path, index=False, encoding="utf-8")
        print(f"[OK] Saved {ticker}: {ticker_path}")
        
        all_frames.append(merged_df)
    
    if not all_frames:
        print("[WARN] No final datasets were built.")
        return pd.DataFrame()
    
    master_df = pd.concat(all_frames, ignore_index=True)
    master_df = master_df.sort_values(["ticker", "date"]).reset_index(drop=True)
    
    # Save master
    master_csv = REPORTS_DIR / "sentiment_decisions_1year.csv"
    master_df.to_csv(master_csv, index=False, encoding="utf-8")
    print(f"\n[OK] Saved master dataset: {master_csv}")
    
    try:
        master_xlsx = REPORTS_DIR / "sentiment_decisions_1year.xlsx"
        master_df.to_excel(master_xlsx, index=False)
        print(f"[OK] Saved Excel: {master_xlsx}")
    except Exception as e:
        print(f"[WARN] Could not save Excel: {e}")
    
    return master_df


def generate_summary_report(sentiment_archive: pd.DataFrame, final_df: pd.DataFrame) -> str:
    """Generate comprehensive summary report."""
    report_lines: List[str] = []
    
    report_lines.append("=" * 80)
    report_lines.append("1-YEAR HISTORICAL NEWS & SENTIMENT ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # News archive summary
    report_lines.append("NEWS ARCHIVE SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Total articles analyzed:             {len(sentiment_archive):,}")
    report_lines.append(f"Date range:                          {sentiment_archive['published_date'].min().date()} to {sentiment_archive['published_date'].max().date()}")
    report_lines.append(f"Average sentiment:                   {sentiment_archive['sentiment'].mean():.4f}")
    report_lines.append(f"Sentiment range:                     [{sentiment_archive['sentiment'].min():.4f}, {sentiment_archive['sentiment'].max():.4f}]")
    report_lines.append("")
    
    # Sentiment distribution by ticker
    report_lines.append("SENTIMENT BY TICKER")
    report_lines.append("-" * 80)
    report_lines.append(f"{'Ticker':<20} {'Articles':>12} {'Mean Sent':>12} {'Std':>10} {'Trend':>10}")
    report_lines.append("-" * 80)
    
    for ticker in TICKERS:
        ticker_articles = sentiment_archive[sentiment_archive["ticker"] == ticker]
        if ticker_articles.empty:
            continue
        
        mean_sent = ticker_articles["sentiment"].mean()
        std_sent = ticker_articles["sentiment"].std()
        article_count = len(ticker_articles)
        
        # Calculate trend (recent vs old)
        mid_point = len(ticker_articles) // 2
        recent_mean = ticker_articles.iloc[-mid_point:]["sentiment"].mean() if mid_point > 0 else mean_sent
        old_mean = ticker_articles.iloc[:mid_point]["sentiment"].mean() if mid_point > 0 else mean_sent
        trend = "↑" if recent_mean > old_mean else "↓" if recent_mean < old_mean else "→"
        
        report_lines.append(f"{ticker:<20} {article_count:>12,} {mean_sent:>12.4f} {std_sent:>10.4f} {trend:>10}")
    
    report_lines.append("")
    
    # Signal summary
    report_lines.append("CURRENT SIGNALS (Latest Date)")
    report_lines.append("-" * 80)
    
    if not final_df.empty:
        latest_date = final_df["date"].max()
        latest_signals = final_df[final_df["date"] == latest_date]
        
        report_lines.append(f"Latest date: {latest_date}")
        report_lines.append(f"{'Ticker':<20} {'Signal':>10} {'Confidence':>12} {'Sentiment':>12} {'Articles':>10}")
        report_lines.append("-" * 80)
        
        for _, row in latest_signals.iterrows():
            report_lines.append(
                f"{row['ticker']:<20} {row['signal']:>10} {row['confidence']:>12.2%} {row['sentiment']:>12.4f} {int(row['article_count']):>10}"
            )
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main() -> None:
    print("[INFO] Building enhanced sentiment analysis from 1-year archive...\n")
    
    # Load archive
    sentiment_archive = load_news_archive()
    if sentiment_archive.empty:
        return
    
    # Compute sentiment
    sentiment_archive = compute_sentiment_archive(sentiment_archive)
    
    # Generate final datasets
    final_df = generate_final_datasets(sentiment_archive)
    
    # Generate report
    if not final_df.empty:
        report = generate_summary_report(sentiment_archive, final_df)
        print("\n" + report)
        
        with open(REPORTS_DIR / "sentiment_summary.txt", "w", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    main()
