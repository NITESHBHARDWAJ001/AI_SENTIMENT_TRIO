from __future__ import annotations

import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import (
    JWT_ACCESS_TOKEN_EXPIRES_HOURS,
    JWT_SECRET_KEY,
    NEWS_SCHEDULER_ENABLED,
    NEWS_SCHEDULER_INTERVAL_MINUTES,
    NEWS_SCHEDULER_RUN_ON_START,
)
from .db import init_db
from .routes.auth_routes import auth_bp
from .routes.public_routes import public_bp
from .routes.user_routes import user_bp
from .services.news_scheduler_service import get_news_scheduler


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=JWT_ACCESS_TOKEN_EXPIRES_HOURS)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173"
                ]
            }
        }
    )
    JWTManager(app)

    init_db()

    scheduler = None
    if NEWS_SCHEDULER_ENABLED and _should_start_background_workers():
        scheduler = get_news_scheduler(
            interval_minutes=NEWS_SCHEDULER_INTERVAL_MINUTES,
            run_on_start=NEWS_SCHEDULER_RUN_ON_START,
        )
        scheduler.start()

    @app.get("/health")
    def health():
        payload = {"status": "ok", "service": "pulsealpha-backend"}
        if scheduler is not None:
            payload["newsScheduler"] = scheduler.status()
        else:
            payload["newsScheduler"] = {"running": False, "reason": "disabled-or-parent-reloader-process"}
        return jsonify(payload)

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(user_bp)

    @app.errorhandler(Exception)
    def handle_exception(error):
        return jsonify({"error": str(error)}), 500

    return app


def _should_start_background_workers() -> bool:
    # In Flask debug mode, avoid starting duplicate scheduler in reloader parent.
    run_main = os.environ.get("WERKZEUG_RUN_MAIN")
    if run_main is None:
        return True
    return run_main == "true"
