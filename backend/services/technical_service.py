from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import RAW_DIR, PROCESSED_DIR


@dataclass
class TechnicalIndicators:
    """Container for technical indicator calculations."""
    ticker: str
    close_price: float
    date: str
    rsi: float | None
    macd: float | None
    signal_line: float | None
    histogram: float | None
    ema_12: float | None
    ema_26: float | None
    buy_sell_signal: str  # "BUY", "SELL", "HOLD"
    explanation: str
    rsi_status: str  # "Oversold", "Overbought", "Neutral"


class TechnicalIndicatorService:
    """Service for calculating technical indicators from stock data."""

    def __init__(self) -> None:
        self.load_error = None
        self.ta = None
        try:
            import pandas_ta as ta
            self.ta = ta
        except ImportError:
            self.load_error = "pandas-ta-classic not installed"

    def calculate_indicators(self, ticker: str) -> TechnicalIndicators | None:
        """
        Calculate technical indicators for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            TechnicalIndicators object or None if ticker not found
        """
        if self.ta is None:
            return self._fallback_indicators(ticker)

        df = self._load_stock_data(ticker)
        if df is None or df.empty:
            return None

        try:
            # Calculate RSI
            rsi = self.ta.rsi(df["Close"], length=14)
            rsi_latest = float(rsi.iloc[-1]) if rsi is not None and len(rsi) > 0 else None

            # Calculate MACD
            macd_result = self.ta.macd(df["Close"], fast=12, slow=26, signal=9)
            macd = None
            signal_line = None
            histogram = None
            if macd_result is not None and len(macd_result) > 0:
                macd_col = macd_result.columns[0] if isinstance(macd_result, pd.DataFrame) else None
                if macd_col is not None:
                    macd = float(macd_result[macd_col].iloc[-1]) if len(macd_result) > 0 else None
                    if len(macd_result.columns) > 1:
                        signal_line = float(macd_result.iloc[-1, 1]) if len(macd_result) > 0 else None
                    if len(macd_result.columns) > 2:
                        histogram = float(macd_result.iloc[-1, 2]) if len(macd_result) > 0 else None

            # Calculate EMA
            ema_12 = self.ta.ema(df["Close"], length=12)
            ema_12_latest = float(ema_12.iloc[-1]) if ema_12 is not None and len(ema_12) > 0 else None

            ema_26 = self.ta.ema(df["Close"], length=26)
            ema_26_latest = float(ema_26.iloc[-1]) if ema_26 is not None and len(ema_26) > 0 else None

            # Get latest price and date
            close_price = float(df["Close"].iloc[-1])
            date_str = str(df.index[-1]) if df.index.name == "Date" else (
                df["Date"].iloc[-1].strftime("%Y-%m-%d") if "Date" in df.columns else "N/A"
            )

            # Generate signal
            signal, explanation, rsi_status = self._generate_signal(rsi_latest, macd, histogram)

            return TechnicalIndicators(
                ticker=ticker,
                close_price=round(close_price, 2),
                date=date_str,
                rsi=round(rsi_latest, 2) if rsi_latest is not None else None,
                macd=round(macd, 4) if macd is not None else None,
                signal_line=round(signal_line, 4) if signal_line is not None else None,
                histogram=round(histogram, 4) if histogram is not None else None,
                ema_12=round(ema_12_latest, 2) if ema_12_latest is not None else None,
                ema_26=round(ema_26_latest, 2) if ema_26_latest is not None else None,
                buy_sell_signal=signal,
                explanation=explanation,
                rsi_status=rsi_status,
            )
        except Exception as e:
            return self._fallback_indicators(ticker, error_msg=str(e))

    def _load_stock_data(self, ticker: str) -> pd.DataFrame | None:
        """Load stock data from CSV files."""
        ticker_upper = ticker.upper().strip()

        # Try processed data first
        processed_path = PROCESSED_DIR / f"{ticker_upper}_final.csv"
        if processed_path.exists():
            try:
                df = pd.read_csv(processed_path)
                if "Close" in df.columns:
                    df = df.sort_values("date" if "date" in df.columns else "Date")
                    return df
            except Exception:
                pass

        # Fall back to raw data
        raw_path = RAW_DIR / f"{ticker_upper}_stock.csv"
        if raw_path.exists():
            try:
                df = pd.read_csv(raw_path)
                if "Close" in df.columns:
                    df = df.sort_values("Date" if "Date" in df.columns else "date")
                    return df
            except Exception:
                pass

        return None

    def _generate_signal(self, rsi: float | None, macd: float | None, histogram: float | None) -> tuple[str, str, str]:
        """
        Generate buy/sell signal based on RSI and optional MACD confirmation.
        
        Returns:
            (signal: "BUY"/"SELL"/"HOLD", explanation: str, rsi_status: str)
        """
        if rsi is None:
            return "HOLD", "Insufficient technical data", "Neutral"

        rsi_status = "Neutral"
        signal = "HOLD"
        explanation = f"RSI at {rsi:.1f} - Market neutral"

        # RSI-based signal
        if rsi < 30:
            rsi_status = "Oversold"
            signal = "BUY"
            explanation = f"RSI {rsi:.1f} indicates oversold conditions - potential bounce"
            
            # MACD confirmation for BUY
            if macd is not None and histogram is not None:
                if histogram > 0:
                    explanation += " + MACD positive histogram confirms upside"
                else:
                    explanation = f"RSI oversold but MACD unclear - cautious BUY"
                    signal = "HOLD"
        elif rsi > 70:
            rsi_status = "Overbought"
            signal = "SELL"
            explanation = f"RSI {rsi:.1f} indicates overbought conditions - potential pullback"
            
            # MACD confirmation for SELL
            if macd is not None and histogram is not None:
                if histogram < 0:
                    explanation += " + MACD negative histogram confirms downside"
                else:
                    explanation = f"RSI overbought but MACD unclear - cautious SELL"
                    signal = "HOLD"
        else:
            # RSI in neutral zone - check MACD for bias
            if macd is not None and histogram is not None:
                if histogram > 0.001:
                    signal = "HOLD"
                    explanation = f"RSI neutral ({rsi:.1f}) but MACD positive - slight upside bias"
                elif histogram < -0.001:
                    signal = "HOLD"
                    explanation = f"RSI neutral ({rsi:.1f}) but MACD negative - slight downside bias"

        return signal, explanation, rsi_status

    def _fallback_indicators(self, ticker: str, error_msg: str = "") -> TechnicalIndicators | None:
        """Fallback when pandas-ta is not available - calculate simple RSI manually."""
        df = self._load_stock_data(ticker)
        if df is None or df.empty:
            return None

        try:
            close_prices = df["Close"].values
            if len(close_prices) < 15:
                return None

            # Simple RSI calculation (2-period for demo)
            rsi = self._calculate_simple_rsi(close_prices, period=14)
            close_price = float(close_prices[-1])
            date_str = str(df.index[-1]) if df.index.name == "Date" else (
                df["Date"].iloc[-1].strftime("%Y-%m-%d") if "Date" in df.columns else "N/A"
            )

            signal, explanation, rsi_status = self._generate_signal(rsi, None, None)

            return TechnicalIndicators(
                ticker=ticker,
                close_price=round(close_price, 2),
                date=date_str,
                rsi=round(rsi, 2),
                macd=None,
                signal_line=None,
                histogram=None,
                ema_12=None,
                ema_26=None,
                buy_sell_signal=signal,
                explanation=explanation,
                rsi_status=rsi_status,
            )
        except Exception as e:
            return None

    @staticmethod
    def _calculate_simple_rsi(prices: list | pd.Series, period: int = 14) -> float:
        """Simple RSI calculation without external library."""
        if isinstance(prices, pd.Series):
            prices = prices.values
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def list_supported_tickers(self) -> list[str]:
        """List all tickers with available data."""
        tickers = set()
        
        # Check processed data
        for file_path in PROCESSED_DIR.glob("*_final.csv"):
            ticker = file_path.stem.replace("_final", "").upper()
            tickers.add(ticker)
        
        # Check raw data
        for file_path in RAW_DIR.glob("*_stock.csv"):
            ticker = file_path.stem.replace("_stock", "").upper()
            tickers.add(ticker)
        
        return sorted(list(tickers))
