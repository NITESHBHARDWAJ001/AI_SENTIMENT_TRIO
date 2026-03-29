import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { motion as Motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { LoadingSkeleton } from "./LoadingSkeleton";

export function TechnicalIndicatorCard({ ticker, compact = false }) {
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticker) {
      setError("No ticker provided");
      setLoading(false);
      return;
    }

    const fetchIndicators = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/technical/${ticker.toUpperCase()}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch technical indicators: ${response.statusText}`);
        }
        const data = await response.json();
        setIndicators(data);
      } catch (err) {
        setError(err.message || "Failed to load technical indicators");
        setIndicators(null);
      } finally {
        setLoading(false);
      }
    };

    fetchIndicators();
  }, [ticker]);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-red-400">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!indicators) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-[var(--text-muted)]">No technical data available</p>
        </CardContent>
      </Card>
    );
  }

  const getSignalBadge = (signal) => {
    const variants = {
      BUY: "positive",
      SELL: "negative",
      HOLD: "neutral"
    };
    return variants[signal] || "info";
  };

  const getSignalIcon = (signal) => {
    switch (signal) {
      case "BUY":
        return <TrendingUp size={14} />;
      case "SELL":
        return <TrendingDown size={14} />;
      default:
        return <Minus size={14} />;
    }
  };

  const getRsiColor = (rsi) => {
    if (!rsi) return "text-[var(--text-muted)]";
    if (rsi < 30) return "text-[#10B981]"; // Buy (green)
    if (rsi > 70) return "text-[#EF4444]"; // Sell (red)
    return "text-[#F59E0B]"; // Hold/neutral (amber)
  };

  const getRsiBgColor = (rsi) => {
    if (!rsi) return "bg-[var(--bg-card)]";
    if (rsi < 30) return "bg-[#10B981]/8";
    if (rsi > 70) return "bg-[#EF4444]/8";
    return "bg-[#F59E0B]/8";
  };

  if (compact) {
    return (
      <Motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Technical Signal</p>
                <Badge variant={getSignalBadge(indicators.signal)} className="gap-1">
                  {getSignalIcon(indicators.signal)}
                  {indicators.signal}
                </Badge>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className={`rounded-lg ${getRsiBgColor(indicators.rsi)} p-3`}>
                  <p className="text-xs text-[var(--text-muted)]">RSI</p>
                  <p className={`text-lg font-semibold ${getRsiColor(indicators.rsi)}`}>
                    {indicators.rsi?.toFixed(1)}
                  </p>
                </div>
                <div className="rounded-lg bg-[var(--bg-card)] p-3">
                  <p className="text-xs text-[var(--text-muted)]">Price</p>
                  <p className="text-lg font-semibold font-mono text-[var(--text-main)]">
                    ${indicators.closePrice?.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-lg bg-[var(--bg-card)] p-3">
                  <p className="text-xs text-[var(--text-muted)]">Date</p>
                  <p className="text-xs font-semibold text-[var(--text-main)]">{indicators.date}</p>
                </div>
              </div>

              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                {indicators.explanation}
              </p>

              {indicators.macd !== null && (
                <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-2">
                  <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                    <div>
                      <p className="text-[var(--text-muted)]">MACD</p>
                      <p className="text-[var(--text-main)]">{indicators.macd?.toFixed(4)}</p>
                    </div>
                    <div>
                      <p className="text-[var(--text-muted)]">Signal</p>
                      <p className="text-[var(--text-main)]">{indicators.signalLine?.toFixed(4)}</p>
                    </div>
                    <div>
                      <p className="text-[var(--text-muted)]">Hist</p>
                      <p className={indicators.histogram > 0 ? "text-[#10B981]" : "text-[#EF4444]"}>
                        {indicators.histogram?.toFixed(4)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </Motion.div>
    );
  }

  return (
    <Motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Technical Analysis</CardTitle>
          <span className="text-xs font-mono text-[var(--text-muted)]">{indicators.ticker}</span>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Main Signal Section */}
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm text-[var(--text-muted)]">Current Signal</p>
              <span className="text-xs text-[var(--text-muted)]">{indicators.date}</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Badge variant={getSignalBadge(indicators.signal)} className="gap-2 px-3 py-2">
                  {getSignalIcon(indicators.signal)}
                  <span className="font-semibold">{indicators.signal}</span>
                </Badge>
              </div>
              <p className="text-sm font-mono text-[var(--text-main)]">
                Close: <span className="font-semibold">${indicators.closePrice?.toFixed(2)}</span>
              </p>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
              {indicators.explanation}
            </p>
          </div>

          {/* RSI Section */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-[var(--text-main)]">Relative Strength Index (RSI)</p>
              <span className="text-xs text-[var(--text-muted)]">14-period</span>
            </div>
            <div className="space-y-2">
              {/* RSI Value */}
              <div className={`rounded-lg ${getRsiBgColor(indicators.rsi)} p-4`}>
                <p className={`text-3xl font-bold ${getRsiColor(indicators.rsi)}`}>
                  {indicators.rsi?.toFixed(1)}
                </p>
              </div>

              {/* RSI Gauge */}
              <div className="overflow-hidden rounded-lg bg-[var(--bg-card)] p-2">
                <div className="h-6 w-full overflow-hidden rounded bg-gradient-to-r from-[#10B981]/20 via-[#F59E0B]/20 to-[#EF4444]/20">
                  <div
                    className="h-full bg-gradient-to-r from-[#10B981] via-[#F59E0B] to-[#EF4444] transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(0, (indicators.rsi || 50) * (100 / 100)))}%` }}
                  />
                </div>
                <div className="mt-1 flex text-xs text-[var(--text-muted)]">
                  <span className="flex-1">0</span>
                  <span className="flex-1 text-center">50</span>
                  <span className="flex-1 text-right">100</span>
                </div>
              </div>

              {/* RSI Status */}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="rounded border border-[#10B981]/40 bg-[#10B981]/8 p-2 text-center">
                  <p className="text-[#10B981]">&lt; 30</p>
                  <p className="text-[var(--text-muted)]">Oversold</p>
                </div>
                <div className="rounded border border-[#F59E0B]/40 bg-[#F59E0B]/8 p-2 text-center">
                  <p className="text-[#F59E0B]">30-70</p>
                  <p className="text-[var(--text-muted)]">Neutral</p>
                </div>
                <div className="rounded border border-[#EF4444]/40 bg-[#EF4444]/8 p-2 text-center">
                  <p className="text-[#EF4444]">&gt; 70</p>
                  <p className="text-[var(--text-muted)]">Overbought</p>
                </div>
              </div>
            </div>
          </div>

          {/* MACD Section */}
          {indicators.macd !== null && (
            <div>
              <p className="mb-2 text-sm font-semibold text-[var(--text-main)]">
                MACD (Moving Average Convergence Divergence)
              </p>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-3">
                  <p className="text-xs text-[var(--text-muted)]">MACD Line</p>
                  <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-main)]">
                    {indicators.macd?.toFixed(4)}
                  </p>
                </div>
                <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-3">
                  <p className="text-xs text-[var(--text-muted)]">Signal Line</p>
                  <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-main)]">
                    {indicators.signalLine?.toFixed(4)}
                  </p>
                </div>
                <div className={`rounded-lg border p-3 ${indicators.histogram > 0 ? "border-[#10B981]/40 bg-[#10B981]/8" : "border-[#EF4444]/40 bg-[#EF4444]/8"}`}>
                  <p className="text-xs text-[var(--text-muted)]">Histogram</p>
                  <p className={`mt-1 font-mono text-sm font-semibold ${indicators.histogram > 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                    {indicators.histogram?.toFixed(4)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* EMA Section */}
          {(indicators.ema12 !== null || indicators.ema26 !== null) && (
            <div>
              <p className="mb-2 text-sm font-semibold text-[var(--text-main)]">
                Exponential Moving Averages
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-3">
                  <p className="text-xs text-[var(--text-muted)]">EMA-12</p>
                  <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-main)]">
                    ${indicators.ema12?.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)]/50 p-3">
                  <p className="text-xs text-[var(--text-muted)]">EMA-26</p>
                  <p className="mt-1 font-mono text-sm font-semibold text-[var(--text-main)]">
                    ${indicators.ema26?.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Data Status */}
          <p className="text-xs text-[var(--text-muted)]">
            Data Status: <span className="capitalize">{indicators.taStatus}</span>
          </p>
        </CardContent>
      </Card>
    </Motion.div>
  );
}
