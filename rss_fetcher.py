"""
RSS news fetcher module for Google News RSS scraping.

Handles:
- Query generation for companies and domain keywords
- RSS feed fetching and parsing
- Article extraction with metadata
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import feedparser


BASE_URL = "https://news.google.com/rss/search?q={}"
SOURCE_NAME = "Google News RSS"


def _normalize_spaces(text: str) -> str:
    """Normalize whitespace in text."""
    return re.sub(r"\s+", " ", text or "").strip()


def _generate_queries(
    ticker: str, company: str, domain_keywords: List[str]
) -> List[str]:
    """
    Generate search queries for a company.

    Args:
        ticker: Stock ticker symbol
        company: Company name
        domain_keywords: Domain-specific keywords

    Returns:
        List of query strings to fetch
    """
    queries = [
        f"{company} stock",
        f"{company} news",
    ]
    
    # Add domain keyword queries
    for keyword in domain_keywords[:3]:  # Limit to 3 domain queries per company
        queries.append(keyword)
    
    return queries


def fetch_rss(query: str, max_results: int = 100) -> List[Dict[str, str]]:
    """
    Fetch and parse Google News RSS for a query.

    Args:
        query: Search string (e.g., 'Tesla stock')
        max_results: Maximum number of entries to keep from feed

    Returns:
        List of article dicts containing title, summary, published, source, query
    """
    rss_url = BASE_URL.format(quote_plus(query))
    
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"[ERROR] Failed to fetch RSS for query '{query}': {e}")
        return []

    rows: List[Dict[str, str]] = []
    
    for entry in feed.entries[:max_results]:
        article = {
            "title": _normalize_spaces(entry.get("title", "")),
            "summary": _normalize_spaces(entry.get("summary", "")),
            "published": _normalize_spaces(entry.get("published", "")),
            "source": SOURCE_NAME,
            "query": query,
        }
        
        # Skip if no title
        if article["title"]:
            rows.append(article)
    
    return rows


def fetch_all_queries(
    tickers: Dict[str, str],
    domain_map: Dict[str, List[str]],
    max_results_per_query: int = 100,
) -> List[Dict[str, str]]:
    """
    Fetch articles for all companies and domain queries.

    Args:
        tickers: Dict mapping ticker -> company name
        domain_map: Dict mapping ticker -> domain keywords
        max_results_per_query: Max articles per query

    Returns:
        Combined list of all fetched articles
    """
    all_articles: List[Dict[str, str]] = []
    query_count = 0
    
    for ticker, company in tickers.items():
        domain_keywords = domain_map.get(ticker, [])
        queries = _generate_queries(ticker, company, domain_keywords)
        
        print(f"[INFO] Processing {ticker} ({company}) - {len(queries)} queries")
        
        for query in queries:
            print(f"  → Fetching: {query}")
            articles = fetch_rss(query, max_results=max_results_per_query)
            all_articles.extend(articles)
            query_count += 1
            print(f"    ✓ Got {len(articles)} articles")
    
    print(f"\n[INFO] Total queries processed: {query_count}")
    print(f"[INFO] Total articles fetched: {len(all_articles)}")
    
    return all_articles
