# Quick Start Guide

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify installation**:
```bash
python -c "import feedparser, pandas, openpyxl; print('✓ All dependencies installed')"
```

## Running the Pipeline

### Basic Usage

```bash
python pipeline_news.py
```

This will:
1. ✓ Fetch news articles from Google News RSS for all 7 companies
2. ✓ Clean and deduplicate the data
3. ✓ Map articles to company tickers
4. ✓ Export results to `data/raw/rss_news.xlsx`

### Example Output

```
================================================================================
NEWS SCRAPING PIPELINE FOR AI STOCK SENTIMENT ANALYZER
================================================================================

Target companies: 7
  • TSLA            Tesla
  • AAPL            Apple
  • GOOGL           Google
  • MSFT            Microsoft
  • RELIANCE.NS     Reliance Industries
  • TCS.NS          Tata Consultancy Services
  • INFY.NS         Infosys

================================================================================
STEP 1: FETCHING RSS ARTICLES
================================================================================

[INFO] Processing TSLA (Tesla) - 5 queries
  → Fetching: Tesla stock
    ✓ Got 95 articles
  → Fetching: Tesla news
    ✓ Got 87 articles
  → Fetching: tesla
    ✓ Got 92 articles
  → Fetching: elon musk
    ✓ Got 78 articles
  → Fetching: ev
    ✓ Got 150 articles

[INFO] Total queries processed: 35
[INFO] Total articles fetched: 3247

================================================================================
STEP 2: CLEANING & DEDUPLICATING
================================================================================

[CLEANING] Raw articles: 3247
[CLEANING] After removing empty titles: 3243
[CLEANING] After date parsing: 3240
[CLEANING] After 730-day filter: 3198
[CLEANING] Removed 415 duplicate titles: 2783 remain
[CLEANING] Removed 128 duplicate content: 2655 remain
[CLEANING] Final cleaned articles: 2655

================================================================================
STEP 3: MAPPING ARTICLES TO COMPANIES
================================================================================

[MAPPING] Mapping 2655 articles...
[MAPPING] Direct matches: 1847
[MAPPING] Domain matches: 808
[MAPPING] Unmapped: 0

[INFO] Removed 0 unmapped articles

================================================================================
STEP 4: PREPARING FINAL OUTPUT
================================================================================

[INFO] Final dataset statistics:
  Total rows: 2655
  Date range: 2024-01-14 to 2022-03-15

  Articles by ticker:
    AAPL            521 articles
    GOOGL           387 articles
    INFY.NS         243 articles
    MSFT            418 articles
    RELIANCE.NS     156 articles
    TCS.NS          189 articles
    TSLA            741 articles

  Mapping type breakdown:
    direct       1847 articles
    domain        808 articles

================================================================================
STEP 5: SAVING TO EXCEL
================================================================================

✓ SUCCESS: Saved to data/raw/rss_news.xlsx
  Shape: 2655 rows × 8 columns

================================================================================
PIPELINE COMPLETED
================================================================================
```

## Output Files

After running the pipeline, you'll find:

```
AI-SENTIMENT-TRIO/
├── pipeline_news.py           (main orchestrator)
├── rss_fetcher.py             (fetching module)
├── cleaner.py                 (cleaning module)
├── mapper.py                  (mapping module)
└── data/
    └── raw/
        └── rss_news.xlsx      ← YOUR FINAL DATA
```

## Excel File Structure

Open `data/raw/rss_news.xlsx` to see:

- **2,655 rows** of news articles
- **8 columns**: title, summary, published, source, query, ticker, mapping_type, text
- **Sorted by date** (newest first)
- **Mapped to 7 companies** using direct and domain matching

### Sample Rows

| title | ticker | mapping_type | published |
|-------|--------|-------------|-----------|
| Tesla Q4 Earnings Exceed Expectations | TSLA | direct | 2024-01-15 |
| EV Market Surges on Battery Innovation | TSLA | domain | 2024-01-14 |
| Apple Announces iOS 18 Features | AAPL | direct | 2024-01-13 |
| ... | ... | ... | ... |

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named feedparser"
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### Issue: "No articles fetched"
**Solution**: 
- Check internet connection
- Google News RSS might have rate limits
- Try again in a few minutes

### Issue: "Excel file not created"
**Solution**:
- Ensure `data/raw/` directory exists
- Check file write permissions
- Pipeline creates CSV fallback automatically

### Issue: Few articles for specific companies
**Solution**:
- Add more domain keywords in `pipeline_news.py`
- Increase `max_results_per_query` parameter
- Some companies may have less news coverage

## Customization Examples

### Increase articles per query (3,500 → 5,600 theoretical max)

In `pipeline_news.py`:
```python
articles = fetch_all_queries(
    tickers=TICKERS,
    domain_map=DOMAIN_MAP,
    max_results_per_query=200,  # Changed from 100
)
```

### Change to 1-year lookback (instead of 2 years)

In `pipeline_news.py`:
```python
df = clean_articles(articles, lookback_days=365)  # Changed from 730
```

### Add a new company

In `pipeline_news.py`:
```python
TICKERS["AMZN"] = "Amazon"

DOMAIN_MAP["AMZN"] = [
    "amazon", 
    "aws", 
    "ecommerce", 
    "cloud computing",
    "retail"
]
```

## Performance Tips

1. **First run takes 2-3 minutes**: RSS fetching is sequential
2. **Subsequent runs**: Add caching to reuse fetched data
3. **Large datasets**: Filter by date using `lookback_days` parameter
4. **Memory usage**: ~500MB for full 2-year dataset

## Next Steps

1. **Review the data**: Open `data/raw/rss_news.xlsx` in Excel/Sheets
2. **Analyze**: Use the `text` column for sentiment analysis
3. **Extend**: Add sentiment scoring to pipeline
4. **Export**: Use `mapping_type` column to track evidence quality

---

**Questions?** Check `PIPELINE_README.md` for detailed documentation.
