"""
Configuration module for the news scraping pipeline.

This file centralizes all configuration including:
- Company tickers and names
- Domain keywords for each company  
- RSS fetching parameters
- Data processing parameters
"""

from typing import Dict, List


# ============================================================================
# COMPANY DEFINITIONS (TOP 7)
# ============================================================================
# Update TICKERS to add/remove companies
# Format: {ticker: company_name}

TICKERS: Dict[str, str] = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "GOOGL": "Google",
    "MSFT": "Microsoft",
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infysys",
}


# ============================================================================
# DOMAIN KEYWORDS FOR EACH COMPANY
# ============================================================================
# Update DOMAIN_MAP to adjust search coverage
# Format: {ticker: [keyword1, keyword2, ...]}
#
# Strategy:
# - Include company name variants
# - Include key executives/leaders
# - Include product names
# - Include industry terms
# - Include competitor/alternative names
#
# These keywords are used to find articles that mention the company
# indirectly (e.g., "EV market" articles for Tesla)

DOMAIN_MAP: Dict[str, List[str]] = {
    "TSLA": [
        "tesla",           # Company name
        "elon musk",       # Key executive
        "ev",              # Product category
        "electric vehicle",  # Product category
        "battery",         # Core technology
    ],
    "AAPL": [
        "apple",           # Company name
        "iphone",          # Key product
        "macbook",         # Key product
        "ios",             # OS
        "tim cook",        # CEO
    ],
    "GOOGL": [
        "google",          # Company name
        "alphabet",        # Parent company
        "youtube",         # Key subsidiary
        "ads",             # Business area
        "search engine",   # Core service
        "ai",              # Strategic focus
    ],
    "MSFT": [
        "microsoft",       # Company name
        "azure",           # Cloud platform
        "windows",         # OS
        "openai",          # Partnership
        "cloud",           # Strategic focus
    ],
    "RELIANCE.NS": [
        "reliance",        # Company name
        "jio",             # Key subsidiary
        "oil",             # Business segment
        "gas",             # Business segment
        "energy",          # Industry
    ],
    "TCS.NS": [
        "tcs",             # Company name
        "tata consultancy",  # Full name
        "it services",     # Industry
        "outsourcing",     # Core service
    ],
    "INFY.NS": [
        "infysys",         # Company name
        "it sector",       # Industry
        "digital services",  # Services
        "consulting",      # Service type
    ],
}


# ============================================================================
# FETCHING PARAMETERS
# ============================================================================

# Maximum articles to fetch per query
# Higher = more articles but slower fetch time
# Recommended: 100 (good balance)
# Range: 10-500
MAX_RESULTS_PER_QUERY = 100

# Base URL for Google News RSS
BASE_URL = "https://news.google.com/rss/search?q={}"

# Source name to include in output
SOURCE_NAME = "Google News RSS"


# ============================================================================
# DATA PROCESSING PARAMETERS
# ============================================================================

# Lookback period in days (2 years = 730 days)
# Articles older than this are discarded
# Recommended: 730 (2 years)
# Options: 180 (6 months), 365 (1 year), 730 (2 years), 1095 (3 years)
LOOKBACK_DAYS = 730

# Keep unmapped articles in final output?
# True = Include articles that couldn't be mapped to a company
# False = Only include mapped articles (default, recommended)
KEEP_UNMAPPED = False

# Remove duplicate articles?
# True = Deduplicate by title and content (default, recommended)
# False = Keep all articles including duplicates
DEDUPLICATE = True


# ============================================================================
# OUTPUT PARAMETERS
# ============================================================================

# Output directory for saved data
OUTPUT_DIR = "data/raw"

# Output filename (Excel)
OUTPUT_FILENAME = "rss_news.xlsx"

# Sheet name in Excel file
SHEET_NAME = "News"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config() -> Dict:
    """Return complete configuration dict."""
    return {
        "tickers": TICKERS,
        "domain_map": DOMAIN_MAP,
        "max_results_per_query": MAX_RESULTS_PER_QUERY,
        "lookback_days": LOOKBACK_DAYS,
        "keep_unmapped": KEEP_UNMAPPED,
        "output": {
            "dir": OUTPUT_DIR,
            "filename": OUTPUT_FILENAME,
            "sheet_name": SHEET_NAME,
        },
    }


def print_config() -> None:
    """Print current configuration."""
    print("\nCURRENT CONFIGURATION")
    print("=" * 80)
    print(f"\nCompanies: {len(TICKERS)}")
    for ticker, company in TICKERS.items():
        keywords = len(DOMAIN_MAP.get(ticker, []))
        print(f"  {ticker:15} {company:30} ({keywords} domain keywords)")
    
    print(f"\nParameters:")
    print(f"  Max results per query: {MAX_RESULTS_PER_QUERY}")
    print(f"  Lookback period: {LOOKBACK_DAYS} days")
    print(f"  Keep unmapped: {KEEP_UNMAPPED}")
    print(f"  Deduplicate: {DEDUPLICATE}")
    
    print(f"\nOutput:")
    print(f"  Directory: {OUTPUT_DIR}")
    print(f"  Filename: {OUTPUT_FILENAME}")
    print(f"  Sheet name: {SHEET_NAME}\n")


if __name__ == "__main__":
    print_config()
