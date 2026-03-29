"""
Company mapping module.

Handles:
- Direct company/ticker name matching
- Domain keyword matching
- Mapping type classification (direct vs domain)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


def _contains_term(text: str, term: str) -> bool:
    """
    Check if term appears as a whole word/phrase in text.

    Args:
        text: Text to search in
        term: Term to find

    Returns:
        True if term found as whole word(s)
    """
    term = re.escape(term.lower().strip())
    if not term:
        return False
    pattern = rf"\b{term}\b"
    return re.search(pattern, text.lower()) is not None


def map_single_article(
    text: str,
    tickers: Dict[str, str],
    domain_map: Dict[str, List[str]],
    preferred_ticker: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Map article text to a company ticker.

    Priority:
    1. If preferred_ticker set: try direct/domain match for that company
    2. Global direct company name or ticker match
    3. Global domain keyword match

    Args:
        text: Combined title + summary (lowercase)
        tickers: Mapping of ticker -> company name
        domain_map: Mapping of ticker -> domain keywords
        preferred_ticker: Optional preferred ticker from query context

    Returns:
        (ticker, mapping_type) where mapping_type in {'direct', 'domain'}
    """
    text_lower = (text or "").lower()

    # Strategy 1: Prefer ticker from query context if set
    if preferred_ticker and preferred_ticker in tickers:
        company_name = tickers[preferred_ticker]
        
        # Direct match: company name or ticker
        if _contains_term(text_lower, company_name.lower()) or _contains_term(
            text_lower, preferred_ticker.lower()
        ):
            return preferred_ticker, "direct"

        # Domain match: keywords
        for keyword in domain_map.get(preferred_ticker, []):
            if _contains_term(text_lower, keyword.lower()):
                return preferred_ticker, "domain"

    # Strategy 2: Global direct company name match
    for ticker, company_name in tickers.items():
        if _contains_term(text_lower, company_name.lower()) or _contains_term(
            text_lower, ticker.lower()
        ):
            return ticker, "direct"

    # Strategy 3: Global domain keyword match
    for ticker, keywords in domain_map.items():
        for keyword in keywords:
            if _contains_term(text_lower, keyword.lower()):
                return ticker, "domain"

    # No match found
    return None, None


def map_articles(
    df: pd.DataFrame,
    tickers: Dict[str, str],
    domain_map: Dict[str, List[str]],
) -> pd.DataFrame:
    """
    Map all articles to company tickers.

    Args:
        df: DataFrame with article data
        tickers: Mapping of ticker -> company name
        domain_map: Mapping of ticker -> domain keywords

    Returns:
        DataFrame with added ticker and mapping_type columns
    """
    print(f"\n[MAPPING] Mapping {len(df)} articles...")
    
    # Map each article
    mapped_results = []
    for text, query in zip(df["text"], df["query"]):
        # Try to extract preferred ticker from query
        preferred_ticker = None
        
        # Check if query contains a company name or ticker
        for ticker, company in tickers.items():
            if company.lower() in query.lower() or ticker.lower() in query.lower():
                preferred_ticker = ticker
                break
        
        ticker, mapping_type = map_single_article(
            text, tickers, domain_map, preferred_ticker
        )
        mapped_results.append({"ticker": ticker, "mapping_type": mapping_type})
    
    # Add mapping results to dataframe
    mapped_df = pd.DataFrame(mapped_results)
    df["ticker"] = mapped_df["ticker"]
    df["mapping_type"] = mapped_df["mapping_type"]
    
    # Count mapping results
    direct_count = (df["mapping_type"] == "direct").sum()
    domain_count = (df["mapping_type"] == "domain").sum()
    unmapped_count = df["ticker"].isna().sum()
    
    print(f"[MAPPING] Direct matches: {direct_count}")
    print(f"[MAPPING] Domain matches: {domain_count}")
    print(f"[MAPPING] Unmapped: {unmapped_count}")
    
    # Add company name
    df["company"] = df["ticker"].map(tickers)
    
    return df
