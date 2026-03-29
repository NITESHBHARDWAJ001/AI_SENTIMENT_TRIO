from __future__ import annotations

from typing import Any


class NewsSentimentService:
    """Scores news sentiment with FinBERT when available, with safe fallback.

    Output score range is normalized to [-1, 1].
    """

    def __init__(self) -> None:
        self._pipeline = None
        self.model_source = "lexicon-fallback"

        try:
            # Lazy optional dependency: backend still runs if transformers is absent.
            from transformers import pipeline  # type: ignore

            self._pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
            )
            self.model_source = "finbert"
        except Exception:
            self._pipeline = None

    def analyze_news(self, title: str | None, summary: str | None) -> dict[str, Any]:
        text = self._build_text(title, summary)
        if not text:
            return {"label": "Neutral", "score": 0.0, "source": self.model_source}

        if self._pipeline is not None:
            try:
                # Keep input bounded for stable latency.
                pred = self._pipeline(text[:1200])[0]
                label_raw = str(pred.get("label", "neutral")).strip().lower()
                confidence = float(pred.get("score", 0.0))
                mapped_label, signed_score = self._map_finbert_output(label_raw, confidence)
                return {
                    "label": mapped_label,
                    "score": round(signed_score, 4),
                    "source": "finbert",
                }
            except Exception:
                # Fall through to lexical fallback.
                pass

        fallback_score = self._lexical_score(text)
        return {
            "label": self._score_to_label(fallback_score),
            "score": round(fallback_score, 4),
            "source": "lexicon-fallback",
        }

    @staticmethod
    def verdict_from_sentiment(score: float) -> str:
        if score > 0.20:
            return "BUY"
        if score < -0.20:
            return "SELL"
        return "HOLD"

    @staticmethod
    def score_from_label(label: str | None) -> float:
        text = str(label or "").strip().lower()
        if "positive" in text or text == "buy":
            return 0.6
        if "negative" in text or text == "sell":
            return -0.6
        return 0.0

    @staticmethod
    def _build_text(title: str | None, summary: str | None) -> str:
        title_part = str(title or "").strip()
        summary_part = str(summary or "").strip()
        return f"{title_part}. {summary_part}".strip(" .")

    @staticmethod
    def _map_finbert_output(label_raw: str, confidence: float) -> tuple[str, float]:
        if "positive" in label_raw:
            return "Positive", max(0.0, min(1.0, confidence))
        if "negative" in label_raw:
            return "Negative", -max(0.0, min(1.0, confidence))
        return "Neutral", 0.0

    @staticmethod
    def _score_to_label(score: float) -> str:
        if score > 0.15:
            return "Positive"
        if score < -0.15:
            return "Negative"
        return "Neutral"

    @staticmethod
    def _lexical_score(text: str) -> float:
        s = text.lower()
        positive_terms = (
            "beat",
            "growth",
            "strong",
            "upgrade",
            "surge",
            "record",
            "profit",
            "bullish",
            "outperform",
            "gain",
            "rally",
        )
        negative_terms = (
            "miss",
            "decline",
            "downgrade",
            "weak",
            "drop",
            "loss",
            "bearish",
            "underperform",
            "lawsuit",
            "risk",
            "fall",
        )

        score = 0.0
        for term in positive_terms:
            if term in s:
                score += 0.12
        for term in negative_terms:
            if term in s:
                score -= 0.12

        return max(-1.0, min(1.0, score))
