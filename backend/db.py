from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Iterable

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema_statements: Iterable[str] = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            target_buy_price REAL,
            notes TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, ticker),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            message TEXT NOT NULL,
            trigger_value REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            url TEXT,
            published_at TEXT,
            sentiment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        ,
        """
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            invested_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, ticker),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        ,
        """
        CREATE TABLE IF NOT EXISTS market_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            company TEXT,
            title TEXT NOT NULL,
            summary TEXT,
            source TEXT,
            link TEXT,
            sentiment TEXT,
            published_at TEXT,
            created_at TEXT NOT NULL
        )
        """
    ]

    with get_connection() as conn:
        for statement in schema_statements:
            conn.execute(statement)
        _ensure_column(conn, "watchlist", "target_buy_price", "REAL")
        _ensure_column(conn, "watchlist", "notes", "TEXT")
        conn.commit()


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    names = {row[1] for row in columns}
    if column not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
