"""
Yahoo Finance stock data pipeline for AI stock sentiment workflows.

What this script does:
- Downloads 2 years of daily OHLCV data for multiple tickers
- Engineers return, momentum, moving-average, and volatility features
- Saves per-ticker raw and processed datasets (CSV)
- Builds master combined dataset (CSV + Excel)

Run:
    python stock_data_pipeline.py
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    tqdm = None


TICKERS: List[str] = [
    "TSLA",
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "JPM",
    "XOM",
    "WMT",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
]

COMPANY_MAP: Dict[str, str] = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta",
    "JPM": "JPMorgan",
    "XOM": "ExxonMobil",
    "WMT": "Walmart",
    "RELIANCE.NS": "Reliance",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
}

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MASTER_CSV = Path("master_stock_dataset.csv")
MASTER_XLSX = Path("master_stock_dataset.xlsx")


def _iter_with_progress(items: List[str], label: str):
    if tqdm is not None:
        return tqdm(items, desc=label, unit="ticker")
    return items


def _safe_write_csv(df: pd.DataFrame, path: Path, overwrite: bool = False) -> bool:
    """Write CSV safely, warning if file exists and overwrite is disabled."""
    if path.exists() and not overwrite:
        print(f"[WARN] File exists, skipped (set overwrite=True to replace): {path}")
        return False
    df.to_csv(path, index=False, encoding="utf-8")
    return True


def _safe_write_excel(df: pd.DataFrame, path: Path, overwrite: bool = False) -> bool:
    """Write Excel safely, warning if file exists and overwrite is disabled."""
    if path.exists() and not overwrite:
        print(f"[WARN] File exists, skipped (set overwrite=True to replace): {path}")
        return False
    try:
        df.to_excel(path, index=False)
        return True
    except Exception as exc:  # pragma: no cover - depends on openpyxl availability
        print(f"[WARN] Could not write Excel file {path}: {exc}")
        return False


def fetch_stock_data(
    ticker: str,
    period: str = "2y",
    interval: str = "1d",
    retries: int = 3,
    backoff_seconds: float = 1.5,
) -> pd.DataFrame:
    """
    Download OHLCV stock data for one ticker using yfinance.

    Returns an empty DataFrame if all retries fail.
    """
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
                threads=False,
                group_by="column",
                multi_level_index=False,
            )
            if df is None or df.empty:
                raise ValueError("No data returned")

            df = df.reset_index()
            # Flatten possible MultiIndex columns from yfinance.
            if isinstance(df.columns, pd.MultiIndex):
                flattened: List[str] = []
                for col in df.columns.to_list():
                    parts = [str(x).strip() for x in col if str(x).strip()]
                    if not parts:
                        flattened.append("")
                        continue
                    if "Date" in parts or "Datetime" in parts:
                        flattened.append("Date")
                        continue

                    # Prefer canonical OHLCV labels if present in any level.
                    canonical = next(
                        (
                            p
                            for p in parts
                            if p in {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
                        ),
                        None,
                    )
                    flattened.append(canonical if canonical else "_".join(parts))
                df.columns = flattened

            # Normalize yfinance variations like Close_TSLA, TSLA_Close, Adj Close.
            normalized_cols: Dict[str, str] = {}
            for col in df.columns:
                col_str = str(col)
                tokenized = col_str.replace("-", "_").replace(" ", "_").split("_")
                tokens = {t.lower() for t in tokenized if t}
                if "date" in tokens or col_str == "Datetime":
                    normalized_cols[col] = "Date"
                elif "open" in tokens:
                    normalized_cols[col] = "Open"
                elif "high" in tokens:
                    normalized_cols[col] = "High"
                elif "low" in tokens:
                    normalized_cols[col] = "Low"
                elif "close" in tokens and "adj" not in tokens:
                    normalized_cols[col] = "Close"
                elif "volume" in tokens:
                    normalized_cols[col] = "Volume"

            # Apply only non-conflicting renames to avoid duplicate labels.
            used_targets = set()
            safe_renames: Dict[str, str] = {}
            for src, dst in normalized_cols.items():
                if dst not in used_targets or src == dst:
                    safe_renames[src] = dst
                    used_targets.add(dst)
            df = df.rename(columns=safe_renames)

            if "Date" not in df.columns and "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})

            required = ["Date", "Open", "High", "Low", "Close", "Volume"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Missing required columns: {missing}; available columns: {list(df.columns)}"
                )

            # Keep only required OHLCV columns and clean date.
            df = df[required].copy()
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
            return df

        except Exception as exc:
            print(f"[WARN] {ticker} download failed (attempt {attempt}/{retries}): {exc}")
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)

    print(f"[ERROR] Failed to download {ticker} after {retries} attempts.")
    return pd.DataFrame()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add return, moving average, momentum, and volatility features."""
    if df.empty:
        return df

    out = df.copy()
    out = out.sort_values("Date").reset_index(drop=True)

    out["return_1d"] = out["Close"].pct_change()
    out["return_5d"] = out["Close"].pct_change(periods=5)
    out["moving_avg_5"] = out["Close"].rolling(window=5, min_periods=5).mean()
    out["moving_avg_10"] = out["Close"].rolling(window=10, min_periods=10).mean()
    out["momentum"] = out["Close"] - out["Close"].shift(5)
    out["volatility"] = out["return_1d"].rolling(window=5, min_periods=5).std()

    return out


def save_data(
    ticker: str,
    raw_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    overwrite: bool = False,
) -> None:
    """Save one ticker's raw and processed datasets."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / f"{ticker}_stock.csv"
    processed_path = PROCESSED_DIR / f"{ticker}_features.csv"

    wrote_raw = _safe_write_csv(raw_df, raw_path, overwrite=overwrite)
    wrote_processed = _safe_write_csv(feature_df, processed_path, overwrite=overwrite)

    if wrote_raw and wrote_processed:
        print(f"Saved {ticker} data")
    else:
        print(f"[INFO] {ticker} output partially or fully skipped due to overwrite protection.")


def build_stock_dataset(
    tickers: Optional[List[str]] = None,
    overwrite: bool = False,
) -> pd.DataFrame:
    """Run full ticker pipeline and return combined feature dataset."""
    tickers = tickers or TICKERS
    all_feature_frames: List[pd.DataFrame] = []

    for ticker in _iter_with_progress(tickers, "Stock pipeline"):
        print(f"Downloading {ticker}...")
        raw_df = fetch_stock_data(ticker)
        if raw_df.empty:
            print(f"[ERROR] Skipping {ticker} due to empty data.")
            continue

        feature_df = add_features(raw_df)
        feature_df["ticker"] = ticker
        feature_df["company_name"] = COMPANY_MAP.get(ticker, ticker)

        save_data(ticker=ticker, raw_df=raw_df, feature_df=feature_df, overwrite=overwrite)
        all_feature_frames.append(feature_df)

    if not all_feature_frames:
        print("[WARN] No ticker datasets were built.")
        return pd.DataFrame()

    master_df = pd.concat(all_feature_frames, ignore_index=True)
    master_df = master_df.sort_values(["ticker", "Date"]).reset_index(drop=True)

    wrote_csv = _safe_write_csv(master_df, MASTER_CSV, overwrite=overwrite)
    wrote_xlsx = _safe_write_excel(master_df, MASTER_XLSX, overwrite=overwrite)

    if wrote_csv:
        print(f"[OK] Saved master CSV: {MASTER_CSV}")
    if wrote_xlsx:
        print(f"[OK] Saved master Excel: {MASTER_XLSX}")

    return master_df


def main() -> None:
    print("[INFO] Starting Yahoo Finance stock pipeline...")
    master_df = build_stock_dataset(tickers=TICKERS, overwrite=False)
    print(f"[INFO] Final combined rows: {len(master_df)}")
    print("[INFO] Pipeline completed.")


if __name__ == "__main__":
    main()
