# AI Stock Sentiment Analyzer - News Scraping Module

A modular news scraping pipeline for fetching and processing financial news articles from Google News RSS, with automatic company/ticker mapping and data export to Excel.

## Overview

This pipeline scrapes news articles for 7 major companies across a 2-year lookback period, maps articles to company tickers using direct and domain-based keyword matching, and exports cleaned data to Excel format.

### Target Companies

| Ticker | Company | Region |
|--------|---------|--------|
| TSLA | Tesla | US |
| AAPL | Apple | US |
| GOOGL | Google | US |
| MSFT | Microsoft | US |
| RELIANCE.NS | Reliance Industries | India |
| TCS.NS | Tata Consultancy Services | India |
| INFY.NS | Infosys | India |

## Architecture

The pipeline is organized into modular components:

### 1. **rss_fetcher.py** - RSS Fetching & Query Generation
- Generates search queries for each company (company name, company ticker, domain keywords)
- Fetches articles from Google News RSS feed
- Returns raw article data with metadata

**Key Functions:**
- `fetch_rss(query, max_results)` - Fetch articles for a single query
- `fetch_all_queries(tickers, domain_map)` - Fetch for all companies/queries

### 2. **cleaner.py** - Data Cleaning & Deduplication
- Parses and validates publication dates
- Filters articles within 2-year lookback period
- Removes duplicates by title and content
- Normalizes text fields

**Key Functions:**
- `clean_articles(articles, lookback_days)` - Clean and filter articles
- `deduplicate_articles(df)` - Remove duplicate entries

### 3. **mapper.py** - Company Mapping
- Maps article text to company tickers using:
  1. **Direct matching**: Company name or ticker in text
  2. **Domain matching**: Domain keywords in text
- Assigns mapping type classification

**Key Functions:**
- `map_single_article(text, tickers, domain_map)` - Map one article
- `map_articles(df, tickers, domain_map)` - Map all articles

### 4. **pipeline_news.py** - Main Orchestrator
- Orchestrates the complete pipeline workflow
- Generates summary statistics
- Exports final data to Excel

## Domain Keywords

Each company has associated domain keywords for broader topic matching:

```python
DOMAIN_MAP = {
    "TSLA": ["tesla", "elon musk", "ev", "electric vehicle", "battery"],
    "AAPL": ["apple", "iphone", "macbook", "ios", "tim cook"],
    "GOOGL": ["google", "alphabet", "youtube", "ads", "search engine", "ai"],
    "MSFT": ["microsoft", "azure", "windows", "openai", "cloud"],
    "RELIANCE.NS": ["reliance", "jio", "oil", "gas", "energy"],
    "TCS.NS": ["tcs", "tata consultancy", "it services", "outsourcing"],
    "INFY.NS": ["infosys", "it sector", "digital services", "consulting"],
}
```

## Query Generation Strategy

For each company, the pipeline generates:
- `"{company} stock"` - Company stock-specific news
- `"{company} news"` - General company news
- Domain queries - Broader topic-based searches (e.g., "EV market", "cloud computing")

This multi-query approach approximates historical coverage across the 2-year window.

## Data Flow

```
┌─────────────────────────────────────┐
│ TICKERS + DOMAIN_MAP                │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ rss_fetcher.py                      │
│ - Generate queries                  │
│ - Fetch from Google News RSS        │
│ - Extract metadata                  │
└─────────────────┬─────────────────────┘
                  │
         [Raw Articles List]
                  │
                  ▼
┌─────────────────────────────────────┐
│ cleaner.py                          │
│ - Parse dates                       │
│ - Filter 2-year window              │
│ - Remove duplicates                 │
│ - Normalize text                    │
└─────────────────┬─────────────────────┘
                  │
         [Cleaned DataFrame]
                  │
                  ▼
┌─────────────────────────────────────┐
│ mapper.py                           │
│ - Direct matching                   │
│ - Domain matching                   │
│ - Assign ticker/type                │
└─────────────────┬─────────────────────┘
                  │
         [Mapped DataFrame]
                  │
                  ▼
┌─────────────────────────────────────┐
│ pipeline_news.py                    │
│ - Orchestrate workflow              │
│ - Generate statistics               │
│ - Export to Excel                   │
└─────────────────┬─────────────────────┘
                  │
                  ▼
        📊 data/raw/rss_news.xlsx
```

## Output Format

The final Excel file (`data/raw/rss_news.xlsx`) contains:

| Column | Description | Example |
|--------|-------------|---------|
| title | Article headline | "Tesla Q4 Earnings Beat Estimates" |
| summary | Article summary/excerpt | "Tesla reported strong quarterly results..." |
| published | Publication date/time | "2024-01-15 10:30:45" |
| source | News source | "Google News RSS" |
| query | Query used to fetch article | "Tesla stock" |
| ticker | Stock ticker | "TSLA" |
| mapping_type | Match type: 'direct' or 'domain' | "direct" |
| text | Lowercase combined title+summary | "tesla q4 earnings beat estimates..." |

## Installation & Usage

### Prerequisites

```bash
pip install feedparser pandas openpyxl
```

### Run the Pipeline

```bash
python pipeline_news.py
```

### Output

The pipeline creates:
- `data/raw/rss_news.xlsx` - Final Excel dataset
- Console output with statistics and progress

## Mapping Strategy

### Priority Order

1. **Preferred Ticker (Query Context)** - If fetching for "Tesla stock", favor Tesla matches
2. **Global Direct Match** - Company name or ticker found in text
3. **Global Domain Match** - Domain keywords found in text
4. **No Match** - Article discarded

### Example Mappings

```
Text: "Tesla announces new EV battery technology"
→ Direct match: "TSLA" (Tesla, EV)

Text: "Alphabet reports ad revenue growth"
→ Direct match: "GOOGL" (Alphabet)

Text: "Cloud computing market reaches new heights, benefits Azure and AWS"
→ Domain match: "MSFT" (Azure keyword)

Text: "Manufacturing sector rebounds"
→ No match (too generic)
```

## Performance Characteristics

- **Queries per company**: ~5 queries (1 company + 1 ticker + domain keywords)
- **Total queries**: ~35 queries for 7 companies
- **Articles per query**: ~100 (max)
- **Total articles fetched**: ~3,500 (max theoretical)
- **Lookback period**: 730 days (2 years)
- **Deduplication**: Title + content-based

## Customization

### Add New Companies

1. Update `TICKERS` dict in `pipeline_news.py`:
```python
TICKERS["NEW_TICKER"] = "Company Name"
```

2. Update `DOMAIN_MAP`:
```python
DOMAIN_MAP["NEW_TICKER"] = ["keyword1", "keyword2", ...]
```

###Change Lookback Period

In `pipeline_news.py`, modify the `clean_articles()` call:
```python
df = clean_articles(articles, lookback_days=365)  # 1 year
```

### Adjust Query Results Limit

In `pipeline_news.py`, modify the fetch call:
```python
articles = fetch_all_queries(
    tickers=TICKERS,
    domain_map=DOMAIN_MAP,
    max_results_per_query=50,  # Increase from 100
)
```

## Troubleshooting

### No articles fetched
- Check internet connection
- Verify Google News RSS is accessible
- RSS feed may have rate limiting applied

### Few articles for some companies
- Domain keywords may be too specific
- Search terms may need adjustment
- Consider adding more domain keywords

### Excel export fails  
- Ensure `openpyxl` is installed: `pip install openpyxl`
- Check file permissions in `data/raw/` directory
- Pipeline will fallback to CSV format

## Future Enhancements

- [ ] Pagination support for deeper historical coverage
- [ ] Alternative RSS sources (financial news sites)
- [ ] Date-based query filtering
- [ ] Sentiment analysis integration
- [ ] Caching/dedup across pipeline runs
- [ ] Concurrent RSS fetching

## Notes

- Google News RSS limits results, so 2-year approximation is "best effort"
- RSS feeds typically show 30-100 most recent items per query
- Multiple query strategies help approximate broader coverage
- Domain keywords enable discovery of indirect company mentions
