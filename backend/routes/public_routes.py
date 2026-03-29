from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..db import get_connection, now_iso
from ..services.data_service import MarketDataService
from ..services.live_signal_service import LiveSignalService
from ..services.model_service import PredictionService
from ..services.news_sentiment_service import NewsSentimentService
from ..services.technical_service import TechnicalIndicatorService

public_bp = Blueprint("public", __name__, url_prefix="/api")

market_data = MarketDataService()
predictor = PredictionService()
technical_indicators = TechnicalIndicatorService()
live_signals = LiveSignalService()
news_sentiment = NewsSentimentService()


@public_bp.get("/overview")
def overview():
    market_data.refresh()
    return jsonify(market_data.overview())


@public_bp.get("/market-summary")
def market_summary():
    market_data.refresh()
    return jsonify(market_data.market_summary())


@public_bp.get("/company/<ticker>")
def company_detail(ticker: str):
    market_data.refresh()
    detail = market_data.company_detail(ticker)
    if not detail:
        return jsonify({"error": "Ticker not found"}), 404
    return jsonify(detail)


@public_bp.get("/company/<ticker>/news")
def company_news(ticker: str):
    market_data.refresh()
    csv_news = market_data.news_feed(ticker=ticker, limit=20)
    db_news = _get_db_news(limit=20, ticker=ticker)
    merged = (db_news + csv_news)[:20]
    return jsonify(_attach_sentiment_and_verdict(merged))


@public_bp.get("/company/<ticker>/sentiment")
def company_sentiment(ticker: str):
    market_data.refresh()
    return jsonify(market_data.company_series(ticker, limit=60))


@public_bp.get("/company/<ticker>/prediction")
def company_prediction(ticker: str):
    market_data.refresh()
    features = market_data.company_features(ticker)
    detail = market_data.company_detail(ticker)
    if not features:
        return jsonify({"error": "Ticker not found"}), 404

    csv_news = market_data.news_feed(ticker=ticker, limit=300)
    enriched_features, news_ctx = live_signals.enrich_features_with_news(
        ticker=ticker,
        base_features=features,
        csv_news_rows=csv_news,
    )

    result = predictor.predict(enriched_features)
    result["ticker"] = ticker
    result["close"] = detail.get("price") if detail else None
    result["liveSentiment"] = {
        "aggregate": news_ctx.aggregate_sentiment,
        "todayNews": news_ctx.today_news,
        "lookbackNews": news_ctx.total_news,
    }
    result["freshness"] = {
        "hasLatestHourReport": news_ctx.has_latest_hour_report,
        "latestPublishedAt": news_ctx.latest_published_at,
        "latestAgeMinutes": news_ctx.latest_age_minutes,
        "refreshTriggered": news_ctx.refresh_triggered,
        "refreshReason": news_ctx.refresh_reason,
    }
    result["verdictBasis"] = (
        "latest-hour-and-history" if news_ctx.has_latest_hour_report else "history-only-stale-latest-hour"
    )
    return jsonify(result)


@public_bp.get("/news")
def news():
    market_data.refresh()
    csv_news = market_data.news_feed(limit=80)
    db_news = _get_db_news(limit=80)
    merged = (db_news + csv_news)[:80]
    return jsonify(_attach_sentiment_and_verdict(merged))


@public_bp.get("/predictions/all")
def all_predictions():
    market_data.refresh()
    companies = market_data.list_companies()
    rows = []
    for company in companies:
        features = market_data.company_features(company["ticker"])
        if not features:
            continue
        csv_news = market_data.news_feed(ticker=company["ticker"], limit=300)
        enriched_features, news_ctx = live_signals.enrich_features_with_news(
            ticker=company["ticker"],
            base_features=features,
            csv_news_rows=csv_news,
        )
        pred = predictor.predict(enriched_features)
        rows.append(
            {
                "ticker": company["ticker"],
                "label": pred["label"],
                "signal": pred["signal"],
                "score": pred.get("final_score", 0),
                "confidence": pred["confidence"],
                "confidence_pct": pred.get("confidence_pct", pred["confidence"]),
                "close": company.get("price", 0),
                "hasLatestHourReport": news_ctx.has_latest_hour_report,
                "todayNews": news_ctx.today_news,
            }
        )
    return jsonify(rows)


@public_bp.get("/model-info")
def model_info():
    return jsonify(predictor.model_info())


@public_bp.get("/technical/<ticker>")
def technical_indicators_endpoint(ticker: str):
    """Get technical indicators (RSI, MACD, EMA) for a stock."""
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        return jsonify({"error": "Ticker is required"}), 400

    indicators = technical_indicators.calculate_indicators(ticker_upper)
    if not indicators:
        return jsonify({"error": f"No data found for ticker {ticker_upper}"}), 404

    return jsonify(
        {
            "ticker": indicators.ticker,
            "date": indicators.date,
            "closePrice": indicators.close_price,
            "rsi": indicators.rsi,
            "rsiStatus": indicators.rsi_status,
            "macd": indicators.macd,
            "signalLine": indicators.signal_line,
            "histogram": indicators.histogram,
            "ema12": indicators.ema_12,
            "ema26": indicators.ema_26,
            "signal": indicators.buy_sell_signal,
            "explanation": indicators.explanation,
            "taStatus": "ready" if technical_indicators.ta else "fallback"
        }
    )


@public_bp.get("/technical/supported")
def technical_supported_tickers():
    """Get list of all tickers with available technical data."""
    tickers = technical_indicators.list_supported_tickers()
    return jsonify({"tickers": tickers, "count": len(tickers)})


@public_bp.get("/news/freshness")
def news_freshness():
    """Report freshness status of RSS/news ingestion for monitoring/scheduling checks."""
    file_health = live_signals.file_news_health()
    return jsonify(file_health)



@public_bp.post("/news/ingest")
def ingest_news():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    computed = news_sentiment.analyze_news(
        title=title,
        summary=str(payload.get("summary", "")).strip(),
    )
    verdict = news_sentiment.verdict_from_sentiment(float(computed.get("score", 0.0)))

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO market_news(
                ticker, company, title, summary, source, link, sentiment, published_at, created_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload.get("ticker", "")).strip().upper() or None,
                str(payload.get("company", "")).strip() or None,
                title,
                str(payload.get("summary", "")).strip() or None,
                str(payload.get("source", "")).strip() or "User Feed",
                str(payload.get("link", "")).strip() or None,
                str(computed.get("label", "Neutral")).strip() or "Neutral",
                str(payload.get("publishedAt", "")).strip() or now_iso(),
                now_iso()
            )
        )
        conn.commit()

    return (
        jsonify(
            {
                "message": "news stored",
                "id": cursor.lastrowid,
                "ticker": str(payload.get("ticker", "")).strip().upper() or None,
                "sentiment": computed.get("label", "Neutral"),
                "sentimentScore": computed.get("score", 0.0),
                "sentimentSource": computed.get("source", "unknown"),
                "verdict": verdict,
            }
        ),
        201,
    )


@public_bp.get("/stocks/search")
def stocks_search():
    market_data.refresh()
    companies = market_data.list_companies()

    q = request.args.get("q", "", type=str).strip().lower()
    min_sentiment = request.args.get("minSentiment", default=-1.0, type=float)
    max_sentiment = request.args.get("maxSentiment", default=1.0, type=float)
    min_change = request.args.get("minChange", default=-100.0, type=float)
    max_change = request.args.get("maxChange", default=100.0, type=float)
    limit = request.args.get("limit", default=30, type=int)
    include_prediction = request.args.get("includePrediction", default="false", type=str).lower() == "true"

    filtered = []
    for item in companies:
        text = f"{item['ticker']} {item['name']}".lower()
        if q and q not in text:
            continue
        if not (min_sentiment <= float(item.get("sentiment", 0.0)) <= max_sentiment):
            continue
        if not (min_change <= float(item.get("change", 0.0)) <= max_change):
            continue

        row = dict(item)
        if include_prediction:
            features = market_data.company_features(item["ticker"])
            if features:
                csv_news = market_data.news_feed(ticker=item["ticker"], limit=300)
                enriched_features, news_ctx = live_signals.enrich_features_with_news(
                    ticker=item["ticker"],
                    base_features=features,
                    csv_news_rows=csv_news,
                )
                pred = predictor.predict(enriched_features)
                row["prediction"] = {
                    "label": pred.get("label"),
                    "confidence": pred.get("confidence"),
                    "modelSource": pred.get("modelSource"),
                    "hasLatestHourReport": news_ctx.has_latest_hour_report,
                    "todayNews": news_ctx.today_news,
                    "newsCount": news_ctx.total_news,
                }
        filtered.append(row)

    return jsonify({"count": len(filtered), "results": filtered[:max(1, min(limit, 100))]})


@public_bp.post("/predict/manual")
def predict_manual():
    payload = request.get_json(silent=True) or {}
    ticker = str(payload.get("ticker", "CUSTOM")).strip().upper() or "CUSTOM"
    company = str(payload.get("company", ticker)).strip() or ticker

    features = {
        "sentiment": float(payload.get("sentiment", 0.0)),
        "return_1d": float(payload.get("return_1d", 0.0)),
        "momentum": float(payload.get("momentum", 0.0)),
        "volatility": float(payload.get("volatility", 0.0))
    }

    result = predictor.predict(features)
    result["ticker"] = ticker
    result["company"] = company
    result["input"] = features
    result["explanation"] = (
        "Prediction generated from entered sentiment, return, momentum, and volatility inputs."
    )
    return jsonify(result)


@public_bp.post("/predict/range")
def predict_range():
    payload = request.get_json(silent=True) or {}
    ticker_input = str(payload.get("ticker", "")).strip().upper()
    company_input = str(payload.get("company", "")).strip()
    start_date = str(payload.get("start_date", "")).strip()
    try:
        range_days = int(payload.get("range_days", 5) or 5)
    except (TypeError, ValueError):
        return jsonify({"error": "range_days must be a valid integer"}), 400

    market_data.refresh()
    ticker = market_data.resolve_ticker(ticker=ticker_input, company=company_input)

    if not ticker or not start_date:
        return jsonify({"error": "Provide valid ticker/company and start_date"}), 400

    if range_days < 1 or range_days > 90:
        return jsonify({"error": "range_days must be between 1 and 90"}), 400

    rows = market_data.company_rows_for_range(ticker=ticker, start_date=start_date, range_days=range_days)
    if not rows:
        return jsonify({"error": "No data found for ticker/date/range"}), 404

    predictions = []
    for row in rows:
        features = {
            "sentiment": row["sentiment"],
            "return_1d": row["return_1d"],
            "momentum": row["momentum"],
            "volatility": row["volatility"]
        }
        pred = predictor.predict(features)
        predictions.append(
            {
                "date": row["date"],
                "ticker": row["ticker"],
                "company": row["company"],
                "close": row["close"],
                "label": pred["label"],
                "signal": pred["signal"],
                "confidence": pred["confidence"],
                "probability": pred["probability"],
                "modelSource": pred.get("modelSource", "unknown")
            }
        )

    return jsonify(
        {
            "ticker": ticker,
            "start_date": start_date,
            "range_days": range_days,
            "count": len(predictions),
            "modelSource": predictions[0].get("modelSource", "unknown"),
            "predictions": predictions
        }
    )


def _get_db_news(limit: int = 80, ticker: str | None = None):
    with get_connection() as conn:
        if ticker:
            rows = conn.execute(
                """
                SELECT id, ticker, company, title, summary, source, link, sentiment, published_at
                FROM market_news
                WHERE UPPER(COALESCE(ticker, '')) = ?
                ORDER BY published_at DESC, created_at DESC
                LIMIT ?
                """,
                (ticker.upper(), limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, ticker, company, title, summary, source, link, sentiment, published_at
                FROM market_news
                ORDER BY published_at DESC, created_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

    mapped = []
    for row in rows:
        mapped.append(
            {
                "id": int(row["id"]),
                "ticker": row["ticker"] or "MARKET",
                "title": row["title"],
                "summary": row["summary"] or "",
                "source": row["source"] or "User Feed",
                "publishedAt": row["published_at"] or "N/A",
                "link": row["link"] or "",
                "sentiment": row["sentiment"] or "Neutral"
            }
        )
    return mapped


def _attach_sentiment_and_verdict(items: list[dict]) -> list[dict]:
    enriched: list[dict] = []
    for item in items:
        row = dict(item)
        existing = str(row.get("sentiment", "")).strip()
        needs_calc = (not existing) or (existing.upper() in {"PENDING", "UNKNOWN", "N/A"})

        if needs_calc:
            scored = news_sentiment.analyze_news(
                title=str(row.get("title", "")),
                summary=str(row.get("summary", "")),
            )
            row["sentiment"] = scored.get("label", "Neutral")
            row["sentimentScore"] = scored.get("score", 0.0)
            row["sentimentSource"] = scored.get("source", "unknown")
        else:
            guessed_score = news_sentiment.score_from_label(existing)
            row["sentimentScore"] = row.get("sentimentScore", guessed_score)
            row["sentimentSource"] = row.get("sentimentSource", "stored-label")

        row["verdict"] = news_sentiment.verdict_from_sentiment(float(row.get("sentimentScore", 0.0)))
        enriched.append(row)
    return enriched
