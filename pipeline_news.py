"""
Main news scraping pipeline orchestrator.

Orchestrates:
- RSS fetching for all companies/domains
- Data cleaning and deduplication
- Company mapping
- Excel export
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from rss_fetcher import fetch_all_queries
from cleaner import clean_articles, deduplicate_articles
from mapper import map_articles
from config import TICKERS, DOMAIN_MAP, MAX_RESULTS_PER_QUERY, LOOKBACK_DAYS, OUTPUT_DIR, OUTPUT_FILENAME


def run_pipeline() -> None:
    """Execute the complete news scraping pipeline."""
    
    print("=" * 80)
    print("NEWS SCRAPING PIPELINE FOR AI STOCK SENTIMENT ANALYZER")
    print("=" * 80)
    print(f"\nTarget companies: {len(TICKERS)}")
    for ticker, company in TICKERS.items():
        print(f"  • {ticker:15} {company}")
    
    # ========================================================================
    # STEP 1: FETCH RSS ARTICLES
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 1: FETCHING RSS ARTICLES")
    print("=" * 80)
    
    articles = fetch_all_queries(
        tickers=TICKERS,
        domain_map=DOMAIN_MAP,
        max_results_per_query=MAX_RESULTS_PER_QUERY,
    )
    
    if not articles:
        print("[ERROR] No articles fetched. Exiting.")
        return
    
    # ========================================================================
    # STEP 2: CLEAN & DEDUPLICATE
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 2: CLEANING & DEDUPLICATING")
    print("=" * 80)
    
    df = clean_articles(articles, lookback_days=LOOKBACK_DAYS)  # 2 years
    df = deduplicate_articles(df)
    
    if len(df) == 0:
        print("[ERROR] No articles after cleaning. Exiting.")
        return
    
    # ========================================================================
    # STEP 3: MAP TO COMPANIES
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 3: MAPPING ARTICLES TO COMPANIES")
    print("=" * 80)
    
    df = map_articles(df, TICKERS, DOMAIN_MAP)
    
    # Remove unmapped articles
    df_mapped = df[df["ticker"].notna()].copy()
    unmapped_count = len(df) - len(df_mapped)
    print(f"\n[INFO] Removed {unmapped_count} unmapped articles")
    
    if len(df_mapped) == 0:
        print("[ERROR] No mapped articles. Exiting.")
        return
    
    # ========================================================================
    # STEP 4: PREPARE FINAL OUTPUT
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 4: PREPARING FINAL OUTPUT")
    print("=" * 80)
    
    # Select and rename columns for final output
    final_df = df_mapped[[
        "title",
        "summary",
        "published",
        "source",
        "query",
        "ticker",
        "mapping_type",
        "text",
    ]].copy()
    
    # Rename columns to match requirements
    final_df.columns = [
        "title",
        "summary",
        "published",
        "source",
        "query",
        "ticker",
        "mapping_type",
        "text",
    ]
    
    # Sort by date (newest first)
    final_df = final_df.sort_values("published", ascending=False).reset_index(drop=True)
    
    print(f"\n[INFO] Final dataset statistics:")
    print(f"  Total rows: {len(final_df)}")
    print(f"  Date range: {final_df['published'].min()} to {final_df['published'].max()}")
    print(f"\n  Articles by ticker:")
    for ticker in sorted(TICKERS.keys()):
        count = (final_df["ticker"] == ticker).sum()
        if count > 0:
            print(f"    {ticker:15} {count:4} articles")
    
    print(f"\n  Mapping type breakdown:")
    for mtype in final_df["mapping_type"].unique():
        count = (final_df["mapping_type"] == mtype).sum()
        if pd.notna(mtype):
            print(f"    {mtype:10} {count:4} articles")
    
    # ========================================================================
    # STEP 5: SAVE TO EXCEL
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 5: SAVING TO EXCEL")
    print("=" * 80)
    
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / OUTPUT_FILENAME
    
    try:
        final_df.to_excel(output_path, index=False, sheet_name="News")
        print(f"\n✓ SUCCESS: Saved to {output_path}")
        print(f"  Shape: {final_df.shape[0]} rows × {final_df.shape[1]} columns")
    except Exception as e:
        print(f"\n✗ ERROR: Failed to save Excel file: {e}")
        # Fallback to CSV
        csv_path = output_dir / "rss_news.csv"
        final_df.to_csv(csv_path, index=False)
        print(f"✓ Fallback: Saved to CSV: {csv_path}")
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
