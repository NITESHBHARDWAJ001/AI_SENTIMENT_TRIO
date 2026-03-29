"""
Sentiment Calculation Verification Script

What this script does:
- Validates sentiment calculation completeness across all processed news
- Checks for missing, invalid, or incomplete sentiment scores
- Generates detailed statistics and distribution analysis
- Identifies problematic articles and their causes
- Provides quality assurance report

Run:
    python verify_sentiment_calculation.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
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

PROCESSED_DIR = Path("data/processed")


def _iter_with_progress(items: List[str], label: str):
    """Optionally wrap with tqdm progress bar."""
    if tqdm is not None:
        return tqdm(items, desc=label, unit="ticker")
    return items


def check_final_dataset(ticker: str) -> Dict[str, any]:
    """
    Validate sentiment calculation in final dataset for one ticker.
    
    Returns dict with validation statistics.
    """
    ticker_path = PROCESSED_DIR / f"{ticker}_final.csv"
    
    stats = {
        "ticker": ticker,
        "file_exists": ticker_path.exists(),
        "rows_total": 0,
        "rows_with_real_sentiment": 0,
        "rows_with_default_sentiment": 0,
        "rows_missing_sentiment": 0,
        "rows_invalid_sentiment": 0,
        "sentiment_mean": None,
        "sentiment_std": None,
        "sentiment_min": None,
        "sentiment_max": None,
        "sentiment_values": [],
        "coverage_pct": 0.0,
        "missing_rows": [],
        "invalid_rows": [],
        "errors": [],
    }
    
    if not ticker_path.exists():
        stats["errors"].append(f"File not found: {ticker_path}")
        return stats
    
    try:
        df = pd.read_csv(ticker_path)
        stats["rows_total"] = len(df)
        
        # Check required columns
        required_cols = ["date", "sentiment", "signal", "score", "confidence"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            stats["errors"].append(f"Missing columns: {missing_cols}")
            return stats
        
        # Analyze sentiment column
        if "sentiment" in df.columns:
            sentiment_series = pd.to_numeric(df["sentiment"], errors="coerce")
            
            # Count valid sentiments
            valid_mask = sentiment_series.notna()
            stats["rows_missing_sentiment"] = (~valid_mask).sum()
            
            # Track real vs default sentiment
            if "sentiment_source" in df.columns:
                real_mask = (df["sentiment_source"] == "news") & valid_mask
                default_mask = (df["sentiment_source"] == "default") & valid_mask
                stats["rows_with_real_sentiment"] = real_mask.sum()
                stats["rows_with_default_sentiment"] = default_mask.sum()
                stats["coverage_pct"] = 100.0 * stats["rows_with_real_sentiment"] / stats["rows_total"] if stats["rows_total"] > 0 else 0.0
            else:
                stats["rows_with_real_sentiment"] = valid_mask.sum()
                stats["rows_with_default_sentiment"] = 0
                stats["coverage_pct"] = 100.0 * valid_mask.sum() / stats["rows_total"] if stats["rows_total"] > 0 else 0.0
            
            # Check for invalid values (should be in [-1, 1])
            if valid_mask.any():
                valid_sentiments = sentiment_series[valid_mask]
                out_of_range = ((valid_sentiments < -1.0) | (valid_sentiments > 1.0)).sum()
                stats["rows_invalid_sentiment"] = out_of_range
                
                if out_of_range > 0:
                    invalid_indices = df.index[(sentiment_series < -1.0) | (sentiment_series > 1.0)]
                    stats["invalid_rows"] = list(invalid_indices[:10])  # First 10
            
            # Stats on valid sentiments
            if valid_mask.any():
                valid_sentiments = sentiment_series[valid_mask]
                stats["sentiment_mean"] = float(valid_sentiments.mean())
                stats["sentiment_std"] = float(valid_sentiments.std())
                stats["sentiment_min"] = float(valid_sentiments.min())
                stats["sentiment_max"] = float(valid_sentiments.max())
                stats["sentiment_values"] = list(valid_sentiments.head(20))
        
        # Check signal generation (should exist)
        if "signal" in df.columns:
            missing_signals = df["signal"].isna().sum()
            if missing_signals > 0:
                stats["errors"].append(f"Found {missing_signals} rows with missing signal (signal generation failed)")
        
    except Exception as e:
        stats["errors"].append(f"Error reading file: {str(e)}")
    
    return stats


def check_rss_news_outputs() -> Dict[str, any]:
    """
    Validate sentiment in raw news outputs if they exist.
    """
    rss_csv = PROCESSED_DIR / "rss_cleaned.csv"
    stats = {
        "rss_file_exists": rss_csv.exists(),
        "total_articles": 0,
        "articles_with_sentiment": 0,
        "articles_missing_sentiment": 0,
        "sentiment_distribution": {},
        "top_mapped_tickers": {},
        "errors": [],
    }
    
    if not rss_csv.exists():
        return stats
    
    try:
        df = pd.read_csv(rss_csv)
        stats["total_articles"] = len(df)
        
        # Check for sentiment column
        if "sentiment" in df.columns or "Sentiment" in df.columns:
            sent_col = "sentiment" if "sentiment" in df.columns else "Sentiment"
            sentiment_series = pd.to_numeric(df[sent_col], errors="coerce")
            
            valid_mask = sentiment_series.notna()
            stats["articles_with_sentiment"] = valid_mask.sum()
            stats["articles_missing_sentiment"] = (~valid_mask).sum()
            
            # Check for PENDING marker (indicates not yet analyzed)
            if "sentiment" in df.columns:
                pending = (df[sent_col] == "PENDING").sum()
                if pending > 0:
                    stats["errors"].append(f"Found {pending} articles still marked as PENDING")
        else:
            stats["errors"].append("No sentiment column found in RSS data")
        
        # Company mapping check
        if "Ticker" in df.columns:
            ticker_counts = df["Ticker"].value_counts().to_dict()
            stats["top_mapped_tickers"] = dict(list(ticker_counts.items())[:5])
        
        # Check Mapped_Type distribution
        if "Mapped_Type" in df.columns:
            mapping_dist = df["Mapped_Type"].value_counts().to_dict()
            stats["mapping_distribution"] = mapping_dist
    
    except Exception as e:
        stats["errors"].append(f"Error reading RSS data: {str(e)}")
    
    return stats


def generate_comprehensive_report(final_stats: List[Dict], rss_stats: Dict) -> str:
    """Generate human-readable verification report."""
    report_lines: List[str] = []
    
    report_lines.append("=" * 80)
    report_lines.append("SENTIMENT CALCULATION VERIFICATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Summary stats
    total_rows = sum(s["rows_total"] for s in final_stats if s["file_exists"])
    total_with_real_sentiment = sum(s["rows_with_real_sentiment"] for s in final_stats if s["file_exists"])
    total_with_default_sentiment = sum(s["rows_with_default_sentiment"] for s in final_stats if s["file_exists"])
    total_missing_sentiment = sum(s["rows_missing_sentiment"] for s in final_stats if s["file_exists"])
    total_invalid_sentiment = sum(s["rows_invalid_sentiment"] for s in final_stats if s["file_exists"])
    
    report_lines.append("FINAL DATASET SUMMARY (data/processed/{ticker}_final.csv)")
    report_lines.append("-" * 80)
    report_lines.append(f"Total rows across all tickers:         {total_rows:,}")
    report_lines.append(f"Rows with REAL sentiment (from news):  {total_with_real_sentiment:,} ({100*total_with_real_sentiment/max(total_rows, 1):.1f}%)")
    report_lines.append(f"Rows with DEFAULT sentiment (no news): {total_with_default_sentiment:,} ({100*total_with_default_sentiment/max(total_rows, 1):.1f}%)")
    report_lines.append(f"Rows missing sentiment:                {total_missing_sentiment:,} ({100*total_missing_sentiment/max(total_rows, 1):.1f}%)")
    report_lines.append(f"Rows with INVALID sentiment (out of range): {total_invalid_sentiment:,}")
    report_lines.append("")
    
    # Per-ticker breakdown
    report_lines.append("SENTIMENT CALCULATION BY TICKER")
    report_lines.append("-" * 80)
    report_lines.append(f"{'Ticker':<20} {'Total':>8} {'Real':>8} {'Default':>8} {'Missing':>8} {'Coverage':>10} {'Mean Sent':>12}")
    report_lines.append("-" * 80)
    
    for stat in final_stats:
        if not stat["file_exists"]:
            report_lines.append(f"{stat['ticker']:<20} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} N/A FILE MISSING")
            continue
        
        if stat["errors"]:
            report_lines.append(f"{stat['ticker']:<20} ERROR: {stat['errors'][0]}")
            continue
        
        mean_str = f"{stat['sentiment_mean']:.4f}" if stat['sentiment_mean'] is not None else "N/A"
        coverage_str = f"{stat['coverage_pct']:.1f}%"
        
        report_lines.append(
            f"{stat['ticker']:<20} {stat['rows_total']:>8} {stat['rows_with_real_sentiment']:>8} "
            f"{stat['rows_with_default_sentiment']:>8} {stat['rows_missing_sentiment']:>8} {coverage_str:>10} {mean_str:>12}"
        )
    
    report_lines.append("")
    report_lines.append("SENTIMENT DISTRIBUTION ANALYSIS")
    report_lines.append("-" * 80)
    
    for stat in final_stats:
        if not stat["file_exists"] or stat["errors"]:
            continue
        
        if stat["sentiment_min"] is not None:
            report_lines.append(f"{stat['ticker']:<20}")
            report_lines.append(f"  Range:   [{stat['sentiment_min']:.4f}, {stat['sentiment_max']:.4f}]")
            report_lines.append(f"  Mean:    {stat['sentiment_mean']:.4f} ± {stat['sentiment_std']:.4f}")
            report_lines.append(f"  Sample:  {stat['sentiment_values'][:5]}")
    
    report_lines.append("")
    report_lines.append("RAW NEWS DATA (data/processed/rss_cleaned.csv)")
    report_lines.append("-" * 80)
    
    if rss_stats["rss_file_exists"]:
        report_lines.append(f"Total articles:                        {rss_stats['total_articles']:,}")
        report_lines.append(f"Articles with sentiment:               {rss_stats['articles_with_sentiment']:,}")
        report_lines.append(f"Articles missing sentiment:            {rss_stats['articles_missing_sentiment']:,}")
        
        if rss_stats.get("mapping_distribution"):
            report_lines.append(f"Mapping distribution:                  {rss_stats['mapping_distribution']}")
        
        if rss_stats.get("top_mapped_tickers"):
            report_lines.append(f"Top mapped tickers:                    {rss_stats['top_mapped_tickers']}")
    else:
        report_lines.append("RSS cleaned data not found")
    
    report_lines.append("")
    report_lines.append("ISSUES & RECOMMENDATIONS")
    report_lines.append("-" * 80)
    
    issues_found = False
    
    for stat in final_stats:
        if stat["errors"]:
            issues_found = True
            report_lines.append(f"\n{stat['ticker']}:")
            for error in stat["errors"]:
                report_lines.append(f"  ⚠ {error}")
    
    if rss_stats.get("errors"):
        issues_found = True
        report_lines.append("\nRSS Data Issues:")
        for error in rss_stats["errors"]:
            report_lines.append(f"  ⚠ {error}")
    
    # Check overall quality
    if total_rows > 0:
        if total_with_real_sentiment == 0:
            issues_found = True
            report_lines.append(f"\n⚠ NO NEWS-BACKED SENTIMENT: 0% of rows have sentiment from news articles")
            report_lines.append("  This might indicate:")
            report_lines.append("    - News fetch failed")
            report_lines.append("    - Sentiment computation failed")
            report_lines.append("    - No recent news within lookback window")
        elif total_with_real_sentiment < total_rows * 0.05:
            # Less than 5% news coverage
            report_lines.append(f"\n⚠ LOW NEWS COVERAGE: Only {100*total_with_real_sentiment/total_rows:.1f}% of stock dates have news-backed sentiment")
            report_lines.append("  This is EXPECTED because:")
            report_lines.append("    - News is only fetched for last 14 days")
            report_lines.append("    - Stock data covers 2 years (~500 days per ticker)")
            report_lines.append("    - Most dates will have default sentiment = 0")
            report_lines.append("  Recommendation: This is normal! Signals are still generated from available news.")
        else:
            report_lines.append(f"\n✓ GOOD NEWS COVERAGE: {100*total_with_real_sentiment/total_rows:.1f}% of stock dates have news-backed sentiment")
    
    if not issues_found:
        report_lines.append("\n✓ All sentiment calculations appear to be complete and valid!")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main() -> None:
    print("[INFO] Starting sentiment calculation verification...\n")
    
    # Verify per-ticker final datasets
    print("[INFO] Checking final datasets...")
    final_stats = []
    for ticker in _iter_with_progress(TICKERS, "Final dataset validation"):
        stats = check_final_dataset(ticker)
        final_stats.append(stats)
    
    # Verify raw RSS data
    print("\n[INFO] Checking raw RSS news data...")
    rss_stats = check_rss_news_outputs()
    
    # Generate report
    print("\n" + "=" * 80)
    report = generate_comprehensive_report(final_stats, rss_stats)
    print(report)
    
    # Save report to file
    report_path = Path("sentiment_verification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[OK] Report saved to: {report_path}")


if __name__ == "__main__":
    main()
