import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { SentimentBadge } from "./SentimentBadge";

export function PredictionCard({ prediction }) {
  const safePrediction = prediction || {
    ticker: "N/A",
    signal: "HOLD",
    label: "Neutral",
    confidence: 0,
    explanation: "No prediction data available."
  };

  const verdictVariant =
    safePrediction.signal === "BUY"
      ? "positive"
      : safePrediction.signal === "SELL"
        ? "negative"
        : "neutral";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Prediction Center</CardTitle>
        <Sparkles size={16} className="text-[#58A6FF]" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--text-muted)]">{safePrediction.ticker}</p>
          <SentimentBadge value={safePrediction.label} />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]/60 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Verdict</p>
          <Badge variant={verdictVariant} className="px-3 py-1 text-[11px] font-semibold">
            {safePrediction.signal || "HOLD"}
          </Badge>
        </div>
        <p className="font-mono text-3xl text-[var(--text-main)]">{Number(safePrediction.confidence || 0).toFixed(1)}%</p>
        <p className="text-sm text-[var(--text-muted)]">{safePrediction.explanation || "No explanation available."}</p>
      </CardContent>
    </Card>
  );
}
