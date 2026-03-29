from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..config import DATA_DIR


@dataclass
class ModelArtifacts:
    model: Any
    metadata: dict
    feature_names: list[str]


class PredictionService:
    def __init__(self) -> None:
        self.model_path = DATA_DIR / "xgboost_model.pkl"
        self.metadata_path = DATA_DIR / "xgboost_metadata.pkl"
        self.artifacts = None
        self.load_error = None
        self.predict_error = None

        try:
            self.artifacts = self._load()
        except Exception as exc:
            self.load_error = str(exc)

    def _load(self) -> ModelArtifacts:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Missing model file: {self.model_path}")

        with open(self.model_path, "rb") as f:
            model = pickle.load(f)

        metadata = {}
        if self.metadata_path.exists():
            with open(self.metadata_path, "rb") as f:
                metadata = pickle.load(f)

        feature_names = metadata.get("features", ["sentiment", "return_1d", "momentum", "volatility"])
        return ModelArtifacts(model=model, metadata=metadata, feature_names=feature_names)

    def predict(self, feature_dict: dict[str, float]) -> dict[str, Any]:
        if self.artifacts is None:
            return self._fallback_predict(feature_dict)

        try:
            breakdown = self._component_breakdown(feature_dict)
            features = [float(feature_dict.get(name, 0.0)) for name in self.artifacts.feature_names]
            X = np.array(features, dtype=float).reshape(1, -1)
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

            if hasattr(self.artifacts.model, "predict_proba"):
                probability = float(self.artifacts.model.predict_proba(X)[0][1])
            else:
                raw = float(self.artifacts.model.predict(X)[0])
                probability = max(0.0, min(1.0, raw))

            confidence = float(abs(probability - 0.5) * 2)
            if probability > 0.60:
                label = "Moderate Bullish"
                signal = "BUY"
            elif probability < 0.40:
                label = "Moderate Bearish"
                signal = "SELL"
            else:
                label = "Neutral"
                signal = "HOLD"

            return {
                "label": label,
                "signal": signal,
                "probability": round(probability, 4),
                "confidence": round(confidence * 100, 2),
                "confidence_pct": round(confidence * 100, 2),
                "featureOrder": self.artifacts.feature_names,
                "modelSource": "dumped_model",
                **breakdown
            }
        except Exception as exc:
            self.predict_error = str(exc)
            return self._fallback_predict(feature_dict)

    def _fallback_predict(self, feature_dict: dict[str, float]) -> dict[str, Any]:
        breakdown = self._component_breakdown(feature_dict)
        sentiment = float(feature_dict.get("sentiment", 0.0))
        momentum = float(feature_dict.get("momentum", 0.0))
        return_1d = float(feature_dict.get("return_1d", 0.0))

        # Lightweight deterministic fallback when model artifact cannot be loaded.
        score = 0.55 + (sentiment * 0.25) + (momentum * 0.01) + (return_1d * 0.8)
        probability = max(0.0, min(1.0, score))
        confidence = abs(probability - 0.5) * 2

        if probability > 0.60:
            label = "Moderate Bullish"
            signal = "BUY"
        elif probability < 0.40:
            label = "Moderate Bearish"
            signal = "SELL"
        else:
            label = "Neutral"
            signal = "HOLD"

        return {
            "label": label,
            "signal": signal,
            "probability": round(probability, 4),
            "confidence": round(confidence * 100, 2),
            "confidence_pct": round(confidence * 100, 2),
            "featureOrder": ["sentiment", "return_1d", "momentum", "volatility"],
            "fallback": True,
            "modelSource": "fallback",
            **breakdown
        }

    def _component_breakdown(self, feature_dict: dict[str, float]) -> dict[str, Any]:
        sentiment_component = float(feature_dict.get("sentiment", 0.0)) * 0.60
        returns_component = float(feature_dict.get("return_1d", 0.0)) * 0.25
        momentum_component = float(feature_dict.get("momentum", 0.0)) * 0.15
        final_score = sentiment_component + returns_component + momentum_component

        if final_score > 0.20:
            explanation = "Positive sentiment and momentum are above threshold, indicating a potential BUY setup."
        elif final_score < -0.20:
            explanation = "Negative sentiment pressure dominates, indicating a potential SELL setup."
        else:
            explanation = "Signals are mixed and near neutral thresholds, suggesting a HOLD stance."

        return {
            "sentiment_component": round(sentiment_component, 4),
            "returns_component": round(returns_component, 4),
            "momentum_component": round(momentum_component, 4),
            "final_score": round(final_score, 4),
            "explanation": explanation
        }

    def model_info(self) -> dict[str, Any]:
        return {
            "sentimentModel": "not-found",
            "predictionModel": str(Path("data") / self.model_path.name),
            "backend": "Flask + SQLite3 + JWT",
            "metadata": self.artifacts.metadata if self.artifacts else {},
            "loadError": self.load_error,
            "predictError": self.predict_error,
            "modelLoaded": self.artifacts is not None
        }
