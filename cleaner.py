"""
Data cleaning and preprocessing module.

Handles:
- Datetime parsing and 2-year filtering
- Deduplication
- Null handling
- Text normalization
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Dict

import pandas as pd


def clean_articles(
    articles: List[Dict[str, str]],
    lookback_days: int = 730,  # 2 years
) -> pd.DataFrame:
    """
    Clean and preprocess articles.

    Args:
        articles: List of raw article dictionaries
        lookback_days: Keep only articles from last N days (default: 730 = 2 years)

    Returns:
        Cleaned DataFrame with valid articles
    """
    if not articles:
        print("[WARN] No articles to clean")
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(articles)
    
    print(f"\n[CLEANING] Raw articles: {len(df)}")
    
    # Normalize text fields
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["summary"] = df["summary"].fillna("").astype(str).str.strip()
    
    # Drop empty titles
    df = df[df["title"] != ""]
    print(f"[CLEANING] After removing empty titles: {len(df)}")
    
    # Parse published date
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    
    # Drop articles without valid dates
    df = df[df["published_dt"].notna()]
    print(f"[CLEANING] After date parsing: {len(df)}")
    
    # Filter by lookback period (last 2 years)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    df = df[df["published_dt"] >= cutoff]
    print(f"[CLEANING] After {lookback_days}-day filter: {len(df)}")
    
    # Remove duplicates by title
    initial_count = len(df)
    df = df.drop_duplicates(subset=["title"], keep="first")
    removed = initial_count - len(df)
    print(f"[CLEANING] Removed {removed} duplicate titles: {len(df)} remain")
    
    # Create combined text field (title + summary)
    df["text"] = (df["title"] + " " + df["summary"]).str.lower()
    
    # Remove duplicates by combined text
    initial_count = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first")
    removed = initial_count - len(df)
    print(f"[CLEANING] Removed {removed} duplicate content: {len(df)} remain")
    
    # Format published date
    df["published"] = df["published_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[CLEANING] Final cleaned articles: {len(df)}\n")
    
    return df


def deduplicate_articles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate articles using multiple strategies.

    Args:
        df: DataFrame with article data

    Returns:
        Deduplicated DataFrame
    """
    initial_count = len(df)
    
    # First pass: exact title match
    df = df.drop_duplicates(subset=["title"], keep="first")
    
    # Second pass: similar text content
    df = df.drop_duplicates(subset=["text"], keep="first")
    
    removed = initial_count - len(df)
    print(f"[INFO] Deduplicated: removed {removed} duplicates")
    
    return df
