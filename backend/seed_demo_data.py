from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd
from werkzeug.security import generate_password_hash

# Allow running as: python backend/seed_demo_data.py from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import PROCESSED_DIR, RAW_DIR  # noqa: E402
from backend.db import get_connection, init_db, now_iso  # noqa: E402


DEMO_USERS = [
    ("Alex Trader", "alex.demo@pulsealpha.ai", "Demo@123"),
    ("Priya Investor", "priya.demo@pulsealpha.ai", "Demo@123"),
    ("Michael Quant", "michael.demo@pulsealpha.ai", "Demo@123"),
    ("Sara Analyst", "sara.demo@pulsealpha.ai", "Demo@123"),
    ("Rohan Growth", "rohan.demo@pulsealpha.ai", "Demo@123"),
]

DEFAULT_TICKERS = [
    "AAPL",
    "MSFT",
    "TSLA",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "JPM",
    "WMT",
    "XOM",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
]


def _load_latest_prices() -> dict[str, float]:
    prices: dict[str, float] = {}
    for path in PROCESSED_DIR.glob("*_final.csv"):
        try:
            df = pd.read_csv(path)
            if df.empty:
                continue
            ticker = str(df["ticker"].iloc[0]) if "ticker" in df.columns else path.stem.replace("_final", "")
            close = float(df.tail(1).iloc[0].get("Close", 0.0))
            if close > 0:
                prices[ticker] = close
        except Exception:
            continue

    # Fallback tickers if processed files are missing.
    for tkr in DEFAULT_TICKERS:
        prices.setdefault(tkr, 100.0)
    return prices


def _upsert_users() -> list[tuple[int, str]]:
    created_users: list[tuple[int, str]] = []
    with get_connection() as conn:
        for name, email, password in DEMO_USERS:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
            if existing:
                user_id = int(existing["id"])
            else:
                cur = conn.execute(
                    "INSERT INTO users(name, email, password_hash, created_at) VALUES(?, ?, ?, ?)",
                    (name, email.lower(), generate_password_hash(password), now_iso()),
                )
                user_id = int(cur.lastrowid)
            created_users.append((user_id, name))
        conn.commit()
    return created_users


def _seed_watchlist_and_portfolio(users: list[tuple[int, str]], prices: dict[str, float]) -> None:
    rng = random.Random(42)
    tickers = sorted(prices.keys())

    with get_connection() as conn:
        for user_id, _name in users:
            user_tickers = rng.sample(tickers, k=min(6, len(tickers)))
            for idx, ticker in enumerate(user_tickers):
                price = float(prices.get(ticker, 100.0))
                target = round(price * (0.94 + (idx * 0.01)), 2)
                conn.execute(
                    """
                    INSERT INTO watchlist(user_id, ticker, target_buy_price, notes, created_at)
                    VALUES(?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, ticker) DO UPDATE SET
                        target_buy_price = excluded.target_buy_price,
                        notes = excluded.notes
                    """,
                    (
                        user_id,
                        ticker,
                        target,
                        f"Demo watch target around support zone for {ticker}",
                        now_iso(),
                    ),
                )

                qty = float(rng.randint(2, 25))
                invested = round(qty * price * rng.uniform(0.85, 1.08), 2)
                conn.execute(
                    """
                    INSERT INTO portfolio_holdings(user_id, ticker, quantity, invested_amount, created_at)
                    VALUES(?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, ticker) DO UPDATE SET
                        quantity = excluded.quantity,
                        invested_amount = excluded.invested_amount
                    """,
                    (user_id, ticker, qty, invested, now_iso()),
                )

            for ticker in user_tickers[:3]:
                conn.execute(
                    "INSERT INTO alerts(user_id, ticker, message, trigger_value, created_at) VALUES(?, ?, ?, ?, ?)",
                    (
                        user_id,
                        ticker,
                        f"Watch {ticker} sentiment shift and breakout confirmation",
                        round(float(prices.get(ticker, 100.0)) * 1.03, 2),
                        now_iso(),
                    ),
                )
        conn.commit()


def _seed_market_news_from_csv(limit: int = 500) -> int:
    csv_path = RAW_DIR / "rss_news.csv"
    if not csv_path.exists():
        return 0

    df = pd.read_csv(csv_path)
    if df.empty:
        return 0

    # Keep relevant tickers + recent rows for performant demo.
    df["Ticker"] = df.get("Ticker", "").astype(str).str.upper()
    df = df[df["Ticker"].isin(DEFAULT_TICKERS)]
    df = df.head(max(50, int(limit))).copy()

    inserted = 0
    with get_connection() as conn:
        existing_keys = {
            (str(row["title"] or "").strip(), str(row["link"] or "").strip())
            for row in conn.execute("SELECT title, link FROM market_news ORDER BY id DESC LIMIT 5000").fetchall()
        }

        for _, row in df.iterrows():
            title = str(row.get("Title", "")).strip()
            link = str(row.get("Link", "")).strip()
            key = (title, link)
            if not title or key in existing_keys:
                continue

            conn.execute(
                """
                INSERT INTO market_news(ticker, company, title, summary, source, link, sentiment, published_at, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row.get("Ticker", "")).strip().upper() or None,
                    str(row.get("Company", "")).strip() or None,
                    title,
                    str(row.get("Summary", "")).strip()[:4000] or None,
                    str(row.get("Source", "Google News RSS")).strip() or "Google News RSS",
                    link or None,
                    str(row.get("sentiment", "Neutral")).strip() or "Neutral",
                    str(row.get("Date", "")).strip() or now_iso(),
                    now_iso(),
                ),
            )
            inserted += 1
            existing_keys.add(key)

        conn.commit()

    return inserted


def _seed_saved_news(users: list[tuple[int, str]]) -> None:
    with get_connection() as conn:
        news_rows = conn.execute(
            """
            SELECT title, summary, source, link, published_at, sentiment
            FROM market_news
            ORDER BY published_at DESC, id DESC
            LIMIT 40
            """
        ).fetchall()

        if not news_rows:
            return

        for user_id, _name in users:
            for row in news_rows[:12]:
                conn.execute(
                    """
                    INSERT INTO saved_news(user_id, title, summary, source, url, published_at, sentiment, created_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        row["title"],
                        row["summary"],
                        row["source"],
                        row["link"],
                        row["published_at"],
                        row["sentiment"],
                        now_iso(),
                    ),
                )
        conn.commit()


def _print_counts() -> None:
    with get_connection() as conn:
        user_count = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        watchlist_count = conn.execute("SELECT COUNT(*) c FROM watchlist").fetchone()["c"]
        portfolio_count = conn.execute("SELECT COUNT(*) c FROM portfolio_holdings").fetchone()["c"]
        alerts_count = conn.execute("SELECT COUNT(*) c FROM alerts").fetchone()["c"]
        market_news_count = conn.execute("SELECT COUNT(*) c FROM market_news").fetchone()["c"]
        saved_news_count = conn.execute("SELECT COUNT(*) c FROM saved_news").fetchone()["c"]

    print("Demo seed summary")
    print(f"- users: {user_count}")
    print(f"- watchlist rows: {watchlist_count}")
    print(f"- portfolio rows: {portfolio_count}")
    print(f"- alerts rows: {alerts_count}")
    print(f"- market_news rows: {market_news_count}")
    print(f"- saved_news rows: {saved_news_count}")


def main() -> None:
    init_db()
    prices = _load_latest_prices()
    users = _upsert_users()
    _seed_watchlist_and_portfolio(users, prices)
    inserted_news = _seed_market_news_from_csv(limit=700)
    _seed_saved_news(users)

    print(f"Inserted market news rows this run: {inserted_news}")
    print("Demo user credentials (all same password): Demo@123")
    for _, name in users:
        print(f"- {name}")
    _print_counts()


if __name__ == "__main__":
    main()
