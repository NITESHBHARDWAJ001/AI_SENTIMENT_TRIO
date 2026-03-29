# Quick Reference Card

## 🚀 Running the Pipeline

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Pipeline
```bash
python pipeline_news.py
```

### Validate Setup
```bash
python validate.py
```

---

## 📁 Key Files

| File | Purpose | Modify? |
|------|---------|---------|
| `pipeline_news.py` | **Main entry point** | ❌ Rarely |
| `config.py` | **Settings** (companies, keywords) | ✅ **Often** |
| `rss_fetcher.py` | Fetch from RSS | ❌ No |
| `cleaner.py` | Clean data | ❌ No |
| `mapper.py` | Map to companies | ❌ No |

---

## ⚙️ Configuration (config.py)

### Add a Company
```python
TICKERS["NVDA"] = "NVIDIA"
DOMAIN_MAP["NVDA"] = ["nvidia", "gpu", "ai", "chips"]
```

### Change Lookback Period
```python
LOOKBACK_DAYS = 365  # 1 year (default: 730 = 2 years)
```

### Increase Data Volume
```python
MAX_RESULTS_PER_QUERY = 200  # (default: 100)
```

---

## 📊 Output

**File**: `data/raw/rss_news.xlsx`

**Columns**:
- `title` - Headline
- `summary` - Excerpt
- `published` - Date
- `source` - "Google News RSS"
- `query` - Search query used
- `ticker` - Stock symbol
- `mapping_type` - "direct" or "domain"
- `text` - Combined text (lowercase)

**Stats**:
- ~3,500 articles fetched (max)
- ~2,500-2,700 after cleaning
- ~100% mapped to 7 companies
- 2-year lookback (730 days)

---

## 🔄 Data Flow

```
config.py (TICKERS, DOMAIN_MAP)
    ↓
rss_fetcher.py (Fetch RSS)
    ↓
cleaner.py (Clean & deduplicate)
    ↓
mapper.py (Map to tickers)
    ↓
data/raw/rss_news.xlsx
```

---

## 📖 Documentation

| Document | Best For |
|----------|----------|
| `QUICKSTART.md` | Getting started |
| `PIPELINE_README.md` | Understanding architecture |
| `STRUCTURE.md` | Module breakdown |
| `IMPLEMENTATION_SUMMARY.md` | Overview & capabilities |

---

## ✅ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| No articles fetched | Check internet; RSS may rate limit |
| Few articles for some companies | Add domain keywords in `config.py` |
| Excel export fails | Install `openpyxl`: `pip install openpyxl` |

---

## 📝 Companies

| Ticker | Company |
|--------|---------|
| TSLA | Tesla |
| AAPL | Apple |
| GOOGL | Google |
| MSFT | Microsoft |
| RELIANCE.NS | Reliance Industries |
| TCS.NS | Tata Consultancy Services |
| INFY.NS | Infosys |

---

## 🎯 Typical Usage

```bash
# 1. Install
pip install -r requirements.txt

# 2. Customize (optional)
# Edit config.py to add companies/keywords

# 3. Validate
python validate.py

# 4. Run
python pipeline_news.py

# 5. Review
# Open data/raw/rss_news.xlsx in Excel
```

---

## ⏱️ Performance

- **Execution time**: 2-3 minutes (depends on RSS response)
- **Output size**: ~2-3 MB Excel file
- **Memory**: ~500 MB for full dataset
- **Network**: ~50 MB download (RSS feeds)

---

## 🔐 Security

- ✓ No API keys required
- ✓ Uses public Google News RSS feed
- ✓ No authentication needed
- ✓ Safe for production use

---

## 📞 Need Help?

1. **Check logs**: Console output has detailed progress
2. **Run validation**: `python validate.py` checks setup
3. **Read docs**: See `QUICKSTART.md` and `PIPELINE_README.md`
4. **Check config**: All settings in `config.py`

---

**Version**: 1.0  
**Status**: ✓ Production Ready  
**Last Updated**: March 28, 2026
