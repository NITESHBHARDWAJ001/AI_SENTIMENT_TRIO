from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_connection, now_iso

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        cursor = conn.execute(
            "INSERT INTO users(name, email, password_hash, created_at) VALUES(?, ?, ?, ?)",
            (name, email, generate_password_hash(password), now_iso())
        )
        user_id = cursor.lastrowid

        defaults = ["AAPL", "MSFT", "TSLA"]
        for ticker in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO watchlist(user_id, ticker, created_at) VALUES(?, ?, ?)",
                (user_id, ticker, now_iso())
            )

        starter_holdings = [
            ("AAPL", 10, 1800.0),
            ("MSFT", 4, 1500.0),
            ("TSLA", 3, 650.0)
        ]
        for ticker, qty, invested in starter_holdings:
            conn.execute(
                """
                INSERT OR IGNORE INTO portfolio_holdings(
                    user_id, ticker, quantity, invested_amount, created_at
                ) VALUES(?, ?, ?, ?, ?)
                """,
                (user_id, ticker, qty, invested, now_iso())
            )

        conn.commit()

    token = create_access_token(identity=str(user_id), additional_claims={"email": email})
    return jsonify({"token": token, "user": {"id": user_id, "name": name, "email": email}}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user["id"]), additional_claims={"email": user["email"]})
    return jsonify(
        {
            "token": token,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        }
    )
