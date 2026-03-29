# Project Structure

```
AI-SENTIMENT-TRIO/
│
├── README.md                          # Original project README
│
├── PIPELINE_README.md                 # Detailed pipeline documentation
├── QUICKSTART.md                      # Quick start guide
│
├── config.py                          # Configuration (CUSTOMIZATION POINT)
│   └── Companies, domain keywords, parameters
│
├── pipeline_news.py                   # Main orchestrator (ENTRY POINT)
│   └── Runs complete pipeline workflow
│
├── rss_fetcher.py                     # RSS fetching module
│   ├── fetch_rss()                    # Fetch single query
│   └── fetch_all_queries()            # Fetch all companies/domains
│
├── cleaner.py                         # Data cleaning module
│   ├── clean_articles()               # Parse, filter, normalize
│   └── deduplicate_articles()         # Remove duplicates
│
├── mapper.py                          # Company mapping module
│   ├── map_single_article()           # Map one article
│   └── map_articles()                 # Map all articles
│
├── requirements.txt                   # Python dependencies
│
├── rss_news_pipeline.py               # Legacy implementation (deprecated)
│
└── data/
    └── raw/
        └── rss_news.xlsx              # OUTPUT: Final Excel file
```

---

## Module Overview

### config.py
**Purpose**: Centralized configuration for the entire pipeline  
**Contains**:
- `TICKERS` - Company definitions
- `DOMAIN_MAP` - Domain keywords for each company
- `MAX_RESULTS_PER_QUERY` - Fetch limit
- `LOOKBACK_DAYS` - Historical window
- Configuration helper functions

**Customize here** to add/remove companies or adjust parameters.

### pipeline_news.py
**Purpose**: Main entry point and orchestrator  
**Does**:
1. Imports configuration from `config.py`
2. Calls `rss_fetcher.fetch_all_queries()` to fetch articles
3. Calls `cleaner.clean_articles()` to clean data
4. Calls `mapper.map_articles()` to map to tickers
5. Generates statistics and summary
6. Calls `save_outputs()` to export Excel

**Run this** to execute the complete pipeline:
```bash
python pipeline_news.py
```

### rss_fetcher.py
**Purpose**: Fetch articles from Google News RSS  
**Functions**:
- `_normalize_spaces()` - Text normalization utility
- `_generate_queries()` - Create search queries for a company
- `fetch_rss(query, max_results)` - Fetch single query
- `fetch_all_queries(tickers, domain_map)` - Fetch all

**Input**: Company tickers and domain keywords  
**Output**: List of raw article dictionaries

### cleaner.py
**Purpose**: Validate, parse, and clean articles  
**Functions**:
- `_normalize_spaces()` - Text normalization
- `clean_articles(articles, lookback_days)` - Main cleaning function
- `deduplicate_articles(df)` - Remove duplicates

**Input**: Raw articles list  
**Output**: Cleaned pandas DataFrame

**Handles**:
- Date parsing and validation
- Lookback period filtering
- Null handling
- Deduplication by title and content

### mapper.py
**Purpose**: Map articles to company tickers  
**Functions**:
- `_contains_term()` - Whole-word matching utility
- `map_single_article()` - Map one article
- `map_articles()` - Map all articles

**Input**: Articles DataFrame, tickers, domain keywords  
**Output**: DataFrame with ticker and mapping_type columns

**Strategy**:
1. Prefer ticker from query context (e.g., "Tesla stock" query → favor TSLA)
2. Try direct name/ticker match globally
3. Try domain keyword match globally
4. Mark as unmapped if no match

---

## Data Flow Visualization

```
pipeline_news.py (ORCHESTRATOR)
    │
    ├─→ config.py
    │   └─ Loads TICKERS, DOMAIN_MAP, parameters
    │
    ├─→ rss_fetcher.fetch_all_queries()
    │   ├─ Generates queries from config
    │   ├─ Fetches from Google News RSS (multiple times)
    │   └─ Returns raw articles list
    │
    ├─→ cleaner.clean_articles()
    │   ├─ Parses dates
    │   ├─ Filters 2-year window
    │   ├─ Removes empty/null values
    │   └─ Returns cleaned DataFrame
    │
    ├─→ cleaner.deduplicate_articles()
    │   ├─ Removes duplicate titles
    │   ├─ Removes duplicate content
    │   └─ Returns deduplicated DataFrame
    │
    ├─→ mapper.map_articles()
    │   ├─ Maps each article to ticker
    │   ├─ Assigns mapping_type (direct/domain)
    │   └─ Returns mapped DataFrame
    │
    └─→ save_outputs()
        └─ data/raw/rss_news.xlsx
```

---

## Customization Workflow

### 1. Add a New Company

**File**: `config.py`

```python
# Add to TICKERS
TICKERS["NEW_TICK"] = "New Company"

# Add to DOMAIN_MAP
DOMAIN_MAP["NEW_TICK"] = [
    "company name",
    "key executive",
    "product name",
    "industry keyword",
]
```

Then run:
```bash
python pipeline_news.py
```

### 2. Change Lookback Period

**File**: `config.py`

```python
LOOKBACK_DAYS = 180  # 6 months instead of 2 years
```

### 3. Increase Article Volume

**File**: `config.py`

```python
MAX_RESULTS_PER_QUERY = 200  # 100 → 200 (2x articles)
```

### 4. Modify Domain Keywords

**File**: `config.py`

```python
DOMAIN_MAP["TSLA"] = [
    "tesla",
    "elon musk",
    "ev",
    "electric vehicle",
    "battery",
    "gigafactory",  # ADD NEW KEYWORD
    "autopilot",     # ADD NEW KEYWORD
]
```

---

## Key Features

✓ **Modular Design** - Each step is independent and can be tested/extended  
✓ **Configurable** - All parameters in one file (`config.py`)  
✓ **Comprehensive Logging** - Progress updates at each step  
✓ **Robust Cleaning** - Multiple deduplication strategies  
✓ **Flexible Mapping** - Direct + domain-based company matching  
✓ **Excel Export** - Ready for external analysis tools  
✓ **2-Year Coverage** - Approximates historical data via multi-query strategy  

---

## Next Steps

1. **Run the pipeline**:
   ```bash
   python pipeline_news.py
   ```

2. **Review the output**:
   ```bash
   # In Excel or Python:
   import pandas as pd
   df = pd.read_excel("data/raw/rss_news.xlsx")
   print(df.head(10))
   ```

3. **Extend the pipeline**:
   - Add sentiment analysis
   - Add caching to avoid re-fetching
   - Add different RSS sources
   - Create visualization dashboards

---

**Questions?** See `QUICKSTART.md` for common issues, or `PIPELINE_README.md` for detailed documentation.
