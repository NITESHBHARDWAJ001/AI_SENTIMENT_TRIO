# AI Stock Market Sentiment Analyzer - 1 Year Historical Analysis

## Overview

This project builds a **comprehensive stock market sentiment analyzer** that:
- Scrapes **1 year of historical news** for 15 major stocks
- Performs sentiment analysis on all articles  
- Merges with stock price data
- Generates BUY/SELL/HOLD trading signals
- Produces actionable insights and reports

---

## 📊 Architecture

### Stage 1: Historical News Archival (NEW!)
**Script:** `historical_news_scraper.py`
- Fetches 1 year of news for all 15 companies
- Uses multiple query variations per company (company name, domain keywords, ticker)
- Deduplicates articles by link and title
- Saves complete archive to `data/archive/news_archive_1year.csv`
- Generates statistics: total articles, coverage per ticker, temporal distribution

**Output:**
```
data/archive/
├── news_archive_1year.csv          (100+ articles per ticker)
└── archive_statistics.txt          (coverage analysis)
```

### Stage 2: Enhanced Sentiment Analysis
**Script:** `sentiment_from_archive.py`
- Loads 1-year news archive
- Computes sentiment for **every historical article**
- Aggregates daily sentiment with statistics (mean, std, min, max)
- Tracks article count per date (confidence booster)
- Merges with historical stock data
- Generates BUY/SELL/HOLD signals with confidence scores

**Output:**
```
data/processed/
├── {ticker}_sentiment_archive.csv  (per-ticker 1-year data)
└── ...

data/reports/
├── sentiment_decisions_1year.csv   (master dataset)
├── sentiment_decisions_1year.xlsx  (Excel export)
└── sentiment_summary.txt           (trading signals summary)
```

### Stage 3: Real-Time Monitoring (Optional)
**Scripts:** `rss_news_pipeline.py`, `sentiment_signal_pipeline.py`
- Fetch recent news (last 14 days)
- Fast sentiment updates for trading decisions
- Can be run daily for alerts

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run the Full 1-Year Pipeline

```bash
# Step 1: Build 1-year news archive (takes 5-10 mins)
python3 historical_news_scraper.py

# Step 2: Compute sentiment and generate signals (takes 10-15 mins)
python3 sentiment_from_archive.py

# Step 3: Verify results
python3 verify_sentiment_calculation.py
```

### Expected Output

**Console Output (Step 1):**
```
[INFO] Building 1-year historical news archive...

[INFO] Scraping TSLA (Tesla) with 21 query variants...
  ✓ company_stock: 85 articles
  ✓ company_price: 62 articles
  ✓ company_news: 78 articles
  ✓ company_earnings: 45 articles
  ✓ ticker_stock: 89 articles
  ✓ domain_price: 55 articles
  ...

[INFO] Total articles before dedup: 15,234
[INFO] Total articles after dedup: 12,456
[INFO] Articles within 365 days: 12,456

[OK] Saved archive: data/archive/news_archive_1year.csv
[OK] Statistics saved to: data/archive/archive_statistics.txt
```

**Archive Statistics:**
```
OVERALL SUMMARY
Total unique articles:                12,456
Date range:                          2025-03-27 to 2026-03-27
Number of tickers:                   15
Number of sources:                   42

ARTICLES PER TICKER
GOOGL                  1,248 articles ( 10.0%)
TSLA                   1,156 articles (  9.3%)
MSFT                   1,089 articles (  8.7%)
AAPL                     987 articles (  7.9%)
...

DECISION-MAKING READINESS
✓ EXCELLENT: Sufficient data for robust sentiment analysis
✓ BALANCED: Good coverage across all tickers
```

**Console Output (Step 2):**
```
[INFO] Building enhanced sentiment analysis from 1-year archive...

[OK] Loaded 12,456 articles from archive

[INFO] Computing sentiment for historical articles...
Sentiment analysis: 100%|███████████████| 12456/12456 [05:23<00:00, 38.58article/s]

[OK] Sentiment range: [-0.9872, 0.9654]
[OK] Mean sentiment: -0.0156

[INFO] Processing TSLA...
[OK] Saved TSLA: data/processed/TSLA_sentiment_archive.csv | 500 dates with 2.34 mean sentiment
[INFO] Processing AAPL...
[OK] Saved AAPL: data/processed/AAPL_sentiment_archive.csv | 500 dates with 0.12 mean sentiment
...

[OK] Saved master dataset: data/reports/sentiment_decisions_1year.csv
[OK] Saved Excel: data/reports/sentiment_decisions_1year.xlsx

================================================================================
1-YEAR HISTORICAL NEWS & SENTIMENT ANALYSIS REPORT
================================================================================

NEWS ARCHIVE SUMMARY
Total articles analyzed:             12,456
Date range:                          2025-03-27 to 2026-03-27
Average sentiment:                   -0.0156
Sentiment range:                     [-0.9872, 0.9654]

CURRENT SIGNALS (Latest Date)
Ticker                Signal    Confidence     Sentiment   Articles
TSLA                   BUY          87.5%         0.3245        15
AAPL                  HOLD          42.1%         0.0123         8
MSFT                   BUY          75.3%         0.2891        12
GOOGL                 SELL          63.8%        -0.1456        10
...
```

---

## 📁 Data Structure

```
e:\new\
├── data/
│   ├── raw/
│   │   ├── TSLA_stock.csv          (2 years OHLCV)
│   │   ├── AAPL_stock.csv
│   │   └── ...
│   ├── archive/
│   │   ├── news_archive_1year.csv  (12K+ articles)
│   │   └── archive_statistics.txt
│   ├── processed/
│   │   ├── TSLA_sentiment_archive.csv  (500 days with sentiment + signals)
│   │   ├── AAPL_sentiment_archive.csv
│   │   └── ...
│   └── reports/
│       ├── sentiment_decisions_1year.csv
│       ├── sentiment_decisions_1year.xlsx
│       └── sentiment_summary.txt
│
├── historical_news_scraper.py      (1-year archive builder)
├── sentiment_from_archive.py       (sentiment + signals from archive)
├── sentiment_signal_pipeline.py    (recent news - 14 days)
├── rss_news_pipeline.py            (news scraping foundation)
├── stock_data_pipeline.py          (stock data downloader)
├── verify_sentiment_calculation.py (quality assurance)
└── requirements.txt
```

---

## 📊 Key Features

### Feature 1: Multi-Query Archival
Per company, we fetch using:
- Company name queries: "{company} stock", "{company} earnings", "{company} news"
- Ticker queries: "{ticker} stock"
- Domain queries: "{keyword} price", "{keyword} market"

**Result:** 100+ articles per ticker, covering all aspects

### Feature 2: Deduplication
- Removes duplicate articles by link
- Removes duplicate articles by title
- Ensures quality, unique dataset

### Feature 3: Sentiment Confidence Weighting
Signal score = 0.6 × (sentiment × article_weight) + 0.25 × return_1d + 0.15 × momentum

Where: **article_weight** = min(1.0, article_count / 10)
- More articles = higher confidence in sentiment
- Few articles = lower weight, conservative signal

### Feature 4: Temporal Aggregation
Daily sentiment includes:
- **sentiment**: mean of all articles that day
- **sentiment_std**: variability across articles
- **sentiment_min/max**: range of opinion
- **article_count**: confidence indicator
- **headlines**: top 3 articles for that day

### Feature 5: Trend Analysis
- Compares recent sentiment vs historical sentiment
- Shows sentiment direction (↑ improving, ↓ declining, → stable)

---

## 🎯 Trading Signals

### Signal Generation Logic

```
score = 0.6 × weighted_sentiment + 0.25 × return_1d + 0.15 × momentum

BUY    if score > 0.2
SELL   if score < -0.2
HOLD   else
```

### Confidence Score

```
confidence = |weighted_sentiment| × (1 - volatility)
```

Higher when:
- Strong news sentiment (positive or negative)
- Low price volatility
- Many supporting articles

---

## 📈 Output Columns

Each `{ticker}_sentiment_archive.csv` contains:

```
date                   YYYY-MM-DD
ticker                 e.g., TSLA
company_name           e.g., Tesla
Close                  Latest closing price
sentiment              [-1, +1] from news articles
sentiment_std          Variability of sentiment
return_1d              Daily % change
momentum               5-day price momentum
volatility             Rolling 5-day std dev
score                  Weighted decision score
signal                 BUY / SELL / HOLD
confidence             Confidence %
article_count          Number of articles that day
```

---

## ⚙️ Customization

### Change Lookback Period
Edit `historical_news_scraper.py`:
```python
archive_df = build_news_archive(tickers=TICKERS, lookback_days=730)  # 2 years
```

### Change Signal Thresholds
Edit `sentiment_from_archive.py`:
```python
BUY_THRESHOLD = 0.3    # More conservative
SELL_THRESHOLD = -0.3
```

### Change Sentiment Weighting
Edit `sentiment_from_archive.py`:
```python
score = 0.7 * weighted_sentiment + 0.2 * return_1d + 0.1 * momentum
```

---

## 🔍 Verification & Quality Assurance

Run verification:
```bash
python3 verify_sentiment_calculation.py
```

Checks for:
- ✓ Sentiment in valid range [-1, 1]
- ✓ No missing signals
- ✓ Article count consistency
- ✓ Data completeness percentage
- ✓ Outliers and anomalies

---

## 📝 Notes

### Why 1 Year?
- Captures seasonal trends (Q1-Q4)
- Enough data for robust patterns (12K+ articles, 100+ per ticker)
- Balances computational load with historical depth

### Google News RSS Limitations
- RSS typically returns last 7-14 days
- Multiple queries with different keywords help capture older articles
- Some historical news may be missed
- Consider supplementing with other sources for critical analysis

### Sentiment Model Chain
1. **FinBERT** (if available) - Financial-focused transformer
2. **VADER** (fallback) - Fast sentiment analysis
3. **Keyword scoring** (final fallback) - Simple but interpretable

---

## 📞 Support

**Common Issues:**

Q: "No articles found"
- A: Check network connection, try later
- A: Google News may block excessive requests

Q: "FinBERT loading fails"
- A: Uses VADER fallback automatically
- A: First FinBERT run downloads model (~500 MB)

Q: "Sentiment all zeros"
- A: Run `historical_news_scraper.py` first
- A: Check `data/archive/news_archive_1year.csv` exists

---

## 📜 License & Credits

Built for AI Stock Sentiment Analysis project.
Uses: feedparser, pandas, yfinance, transformers, VADER, tqdm

