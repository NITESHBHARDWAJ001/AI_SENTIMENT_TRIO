from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..db import get_connection, now_iso
from ..services.data_service import MarketDataService
from ..services.live_signal_service import LiveSignalService
from ..services.model_service import PredictionService

user_bp = Blueprint("user", __name__, url_prefix="/api")
market_data = MarketDataService()
prediction_service = PredictionService()
live_signals = LiveSignalService()


def _user_id() -> int:
    return int(get_jwt_identity())


@user_bp.get("/watchlist")
@jwt_required()
def get_watchlist():
    user_id = _user_id()
    market_data.refresh()
    market_map = {row["ticker"]: row for row in market_data.list_companies()}

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ticker, target_buy_price, notes, created_at FROM watchlist WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()

    enriched = []
    for row in rows:
        ticker = row["ticker"]
        market = market_map.get(ticker, {})
        csv_news = market_data.news_feed(ticker=ticker, limit=80)
        _, news_ctx = live_signals.enrich_features_with_news(
            ticker=ticker,
            base_features=market_data.company_features(ticker) or {},
            csv_news_rows=csv_news,
        )
        latest_message = (
            f"{ticker}: {news_ctx.today_news} articles today, {news_ctx.total_news} in {news_ctx.lookback_days}d. "
            f"Latest report age: {news_ctx.latest_age_minutes if news_ctx.latest_age_minutes is not None else 'N/A'} min."
        )
        enriched.append(
            {
                "ticker": ticker,
                "created_at": row["created_at"],
                "targetBuyPrice": row["target_buy_price"],
                "notes": row["notes"],
                "price": market.get("price", 0),
                "change": market.get("change", 0),
                "sentiment": market.get("sentimentLabel", "Neutral"),
                "hasLatestHourReport": news_ctx.has_latest_hour_report,
                "latestNewsMessage": latest_message,
            }
        )

    return jsonify(enriched)


@user_bp.post("/watchlist")
@jwt_required()
def add_watchlist():
    user_id = _user_id()
    payload = request.get_json(silent=True) or {}
    ticker = str(payload.get("ticker", "")).strip().upper()
    target_buy_price = payload.get("targetBuyPrice")
    notes = str(payload.get("notes", "")).strip() or None
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    target_value = None
    if target_buy_price is not None and str(target_buy_price).strip() != "":
        target_value = float(target_buy_price)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO watchlist(user_id, ticker, target_buy_price, notes, created_at)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                target_buy_price = COALESCE(excluded.target_buy_price, watchlist.target_buy_price),
                notes = COALESCE(excluded.notes, watchlist.notes)
            """,
            (user_id, ticker, target_value, notes, now_iso())
        )
        conn.commit()

    return jsonify({"message": "watchlist updated", "ticker": ticker})


@user_bp.delete("/watchlist/<ticker>")
@jwt_required()
def remove_watchlist(ticker: str):
    user_id = _user_id()
    with get_connection() as conn:
        conn.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker.upper()))
        conn.commit()
    return jsonify({"message": "watchlist removed", "ticker": ticker.upper()})


@user_bp.get("/watchlist/progress")
@jwt_required()
def watchlist_progress():
    user_id = _user_id()
    market_data.refresh()

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ticker, target_buy_price, notes FROM watchlist WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()

    output = []
    for row in rows:
        ticker = row["ticker"]
        detail = market_data.company_detail(ticker) or {"price": 0, "sentimentLabel": "Neutral"}
        current_price = float(detail.get("price", 0))
        target = row["target_buy_price"]
        distance = None
        buy_zone = False
        if target is not None:
            distance = round(current_price - float(target), 2)
            buy_zone = current_price <= float(target)

        features = market_data.company_features(ticker)
        prediction = None
        if features:
            csv_news = market_data.news_feed(ticker=ticker, limit=300)
            enriched_features, news_ctx = live_signals.enrich_features_with_news(
                ticker=ticker,
                base_features=features,
                csv_news_rows=csv_news,
            )
            prediction = prediction_service.predict(enriched_features)
            prediction["hasLatestHourReport"] = news_ctx.has_latest_hour_report
            prediction["todayNews"] = news_ctx.today_news
            prediction["newsCount"] = news_ctx.total_news
            prediction["newsSentiment"] = news_ctx.aggregate_sentiment
            prediction["latestNewsMessage"] = (
                f"{news_ctx.today_news} articles today, {news_ctx.total_news} in last {news_ctx.lookback_days} days"
            )

        output.append(
            {
                "ticker": ticker,
                "currentPrice": round(current_price, 2),
                "targetBuyPrice": target,
                "distanceToTarget": distance,
                "buyZone": buy_zone,
                "sentiment": detail.get("sentimentLabel", "Neutral"),
                "notes": row["notes"],
                "prediction": prediction
            }
        )

    return jsonify(output)


@user_bp.get("/alerts")
@jwt_required()
def get_alerts():
    user_id = _user_id()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, ticker, message, trigger_value, created_at as time FROM alerts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@user_bp.post("/alerts")
@jwt_required()
def create_alert():
    user_id = _user_id()
    payload = request.get_json(silent=True) or {}
    ticker = str(payload.get("ticker", "")).strip().upper()
    message = str(payload.get("message", "")).strip()
    trigger_value = payload.get("trigger_value")

    if not ticker or not message:
        return jsonify({"error": "ticker and message are required"}), 400

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO alerts(user_id, ticker, message, trigger_value, created_at) VALUES(?, ?, ?, ?, ?)",
            (user_id, ticker, message, trigger_value, now_iso())
        )
        conn.commit()

    return jsonify({"message": "alert created"}), 201


@user_bp.delete("/alerts/<int:alert_id>")
@jwt_required()
def delete_alert(alert_id: int):
    user_id = _user_id()
    with get_connection() as conn:
        conn.execute("DELETE FROM alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
        conn.commit()
    return jsonify({"message": "alert deleted", "id": alert_id})


@user_bp.get("/profile")
@jwt_required()
def get_profile():
    user_id = _user_id()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(dict(user))


@user_bp.put("/profile")
@jwt_required()
def update_profile():
    user_id = _user_id()
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()

    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET name = ?, email = ? WHERE id = ?",
            (name, email, user_id)
        )
        conn.commit()

    return jsonify({"message": "profile updated", "user": {"id": user_id, "name": name, "email": email}})


@user_bp.get("/portfolio")
@jwt_required()
def get_portfolio():
    user_id = _user_id()
    market_data.refresh()
    market_map = {row["ticker"]: row for row in market_data.list_companies()}

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticker, quantity, invested_amount, created_at
            FROM portfolio_holdings
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

    holdings = []
    total_invested = 0.0
    total_current = 0.0

    for row in rows:
        ticker = row["ticker"]
        qty = float(row["quantity"])
        invested = float(row["invested_amount"])
        market_price = float(market_map.get(ticker, {}).get("price", 0.0))
        current_value = qty * market_price
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100.0) if invested else 0.0

        total_invested += invested
        total_current += current_value

        holdings.append(
            {
                "ticker": ticker,
                "quantity": qty,
                "investedAmount": round(invested, 2),
                "currentPrice": round(market_price, 2),
                "currentValue": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnlPct": round(pnl_pct, 2),
                "created_at": row["created_at"]
            }
        )

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100.0) if total_invested else 0.0

    return jsonify(
        {
            "holdings": holdings,
            "summary": {
                "totalInvested": round(total_invested, 2),
                "currentValue": round(total_current, 2),
                "totalPnl": round(total_pnl, 2),
                "totalPnlPct": round(total_pnl_pct, 2)
            }
        }
    )


@user_bp.post("/portfolio")
@jwt_required()
def add_portfolio_holding():
    user_id = _user_id()
    payload = request.get_json(silent=True) or {}

    ticker = str(payload.get("ticker", "")).strip().upper()
    quantity = float(payload.get("quantity", 0) or 0)
    invested_amount = float(payload.get("investedAmount", 0) or 0)

    if not ticker or quantity <= 0 or invested_amount <= 0:
        return jsonify({"error": "ticker, quantity, investedAmount are required and must be > 0"}), 400

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_holdings(user_id, ticker, quantity, invested_amount, created_at)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                quantity = excluded.quantity,
                invested_amount = excluded.invested_amount
            """,
            (user_id, ticker, quantity, invested_amount, now_iso())
        )
        conn.commit()

    return jsonify({"message": "portfolio updated", "ticker": ticker}), 201
