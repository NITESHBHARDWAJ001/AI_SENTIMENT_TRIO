"""
Validation and testing utilities for the news scraping pipeline.

Provides functions to:
- Test individual modules
- Validate data quality
- Generate test reports
"""

import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd


def test_imports() -> bool:
    """Test that all required modules can be imported."""
    print("\n" + "=" * 80)
    print("TEST 1: VALIDATING IMPORTS")
    print("=" * 80)
    
    modules = ["feedparser", "pandas", "openpyxl"]
    failed = []
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n[ERROR] {len(failed)} module(s) failed to import")
        print(f"[FIX] Run: pip install -r requirements.txt")
        return False
    
    print(f"\n✓ All imports successful\n")
    return True


def test_pipeline_modules() -> bool:
    """Test that local pipeline modules can be imported."""
    print("\n" + "=" * 80)
    print("TEST 2: VALIDATING PIPELINE MODULES")
    print("=" * 80)
    
    modules = [
        ("config", ["TICKERS", "DOMAIN_MAP"]),
        ("rss_fetcher", ["fetch_rss", "fetch_all_queries"]),
        ("cleaner", ["clean_articles", "deduplicate_articles"]),
        ("mapper", ["map_single_article", "map_articles"]),
    ]
    
    failed = []
    
    for module_name, attributes in modules:
        try:
            module = __import__(module_name)
            print(f"✓ {module_name}")
            
            for attr in attributes:
                if hasattr(module, attr):
                    print(f"  ✓ {attr}")
                else:
                    print(f"  ✗ {attr} NOT FOUND")
                    failed.append(f"{module_name}.{attr}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n[ERROR] {len(failed)} module(s) have issues")
        return False
    
    print(f"\n✓ All modules validated\n")
    return True


def test_config() -> bool:
    """Validate configuration."""
    print("\n" + "=" * 80)
    print("TEST 3: VALIDATING CONFIGURATION")
    print("=" * 80)
    
    try:
        from config import TICKERS, DOMAIN_MAP, get_config
        
        config = get_config()
        
        print(f"Companies: {len(TICKERS)}")
        for ticker, company in TICKERS.items():
            print(f"  ✓ {ticker:15} {company}")
        
        print(f"\nDomain keywords:")
        for ticker, keywords in DOMAIN_MAP.items():
            if ticker in TICKERS:
                print(f"  ✓ {ticker:15} {len(keywords)} keywords")
            else:
                print(f"  ✗ {ticker:15} NOT IN TICKERS")
                return False
        
        print(f"\n✓ Configuration valid\n")
        return True
    
    except Exception as e:
        print(f"✗ Configuration error: {e}\n")
        return False


def test_output_directory() -> bool:
    """Test that output directory can be created."""
    print("\n" + "=" * 80)
    print("TEST 4: VALIDATING OUTPUT DIRECTORY")
    print("=" * 80)
    
    try:
        output_path = Path("data/raw")
        output_path.mkdir(parents=True, exist_ok=True)
        
        test_file = output_path / ".test_write"
        test_file.touch()
        test_file.unlink()
        
        print(f"Output directory: {output_path}")
        print(f"✓ Directory writable")
        print(f"\n✓ Output directory validated\n")
        return True
    
    except Exception as e:
        print(f"✗ Output directory error: {e}")
        print(f"[FIX] Check permissions in current directory\n")
        return False


def validate_excel_output(file_path: str) -> bool:
    """Validate Excel output file."""
    print("\n" + "=" * 80)
    print(f"VALIDATING EXCEL OUTPUT: {file_path}")
    print("=" * 80)
    
    try:
        if not Path(file_path).exists():
            print(f"✗ File not found: {file_path}\n")
            return False
        
        df = pd.read_excel(file_path)
        
        print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"\nColumns:")
        for col in df.columns:
            print(f"  ✓ {col}")
        
        print(f"\nData validation:")
        
        # Check for required columns
        required_cols = ["title", "summary", "published", "source", "query", "ticker", "mapping_type", "text"]
        for col in required_cols:
            if col in df.columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} MISSING")
                return False
        
        # Check data quality
        print(f"\nData quality:")
        print(f"  Non-null titles: {df['title'].notna().sum()} / {len(df)}")
        print(f"  Non-null tickers: {df['ticker'].notna().sum()} / {len(df)}")
        print(f"  Non-null dates: {df['published'].notna().sum()} / {len(df)}")
        
        # Count by mapping type
        print(f"\nMapping type breakdown:")
        for mtype in df['mapping_type'].unique():
            count = (df['mapping_type'] == mtype).sum()
            print(f"  {mtype}: {count}")
        
        # Count by ticker
        print(f"\nArticles by ticker:")
        ticker_counts = df['ticker'].value_counts()
        for ticker, count in ticker_counts.items():
            print(f"  {ticker}: {count}")
        
        print(f"\n✓ Excel output validated\n")
        return True
    
    except Exception as e:
        print(f"✗ Excel validation error: {e}\n")
        return False


def run_all_tests() -> bool:
    """Run all validation tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " PIPELINE VALIDATION TEST SUITE ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    tests = [
        ("Imports", test_imports),
        ("Pipeline modules", test_pipeline_modules),
        ("Configuration", test_config),
        ("Output directory", test_output_directory),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] {test_name} test crashed: {e}\n")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name:30} {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print(f"\n✓ ALL TESTS PASSED - Pipeline is ready to run!")
        print(f"\nRun: python pipeline_news.py\n")
        return True
    else:
        print(f"\n✗ SOME TESTS FAILED - Fix issues before running pipeline\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if success else 1)
