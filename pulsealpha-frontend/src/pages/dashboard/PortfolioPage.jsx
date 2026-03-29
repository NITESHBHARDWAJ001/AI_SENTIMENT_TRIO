import { useEffect, useState } from "react";
import { PredictionCard } from "../../components/common/PredictionCard";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { getAllPredictions } from "../../services/publicService";
import { getPortfolio, upsertPortfolioHolding } from "../../services/userService";

export function PortfolioPage() {
  const [portfolio, setPortfolio] = useState({ holdings: [], summary: {} });
  const [predictions, setPredictions] = useState([]);
  const [form, setForm] = useState({ ticker: "", quantity: "", investedAmount: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    Promise.all([getPortfolio(), getAllPredictions()]).then(([portfolioData, predictionRows]) => {
      if (mounted) {
        setPortfolio(portfolioData || { holdings: [], summary: {} });
        setPredictions(Array.isArray(predictionRows) ? predictionRows : []);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await upsertPortfolioHolding({
      ticker: form.ticker,
      quantity: Number(form.quantity),
      investedAmount: Number(form.investedAmount)
    });
    setForm({ ticker: "", quantity: "", investedAmount: "" });
    const [portfolioData, predictionRows] = await Promise.all([getPortfolio(), getAllPredictions()]);
    setPortfolio(portfolioData || { holdings: [], summary: {} });
    setPredictions(Array.isArray(predictionRows) ? predictionRows : []);
    setSaving(false);
  };

  const predictionMap = new Map((predictions || []).map((row) => [String(row.ticker || "").toUpperCase(), row]));
  const portfolioPredictions = (portfolio.holdings || []).map((row) => {
    const ticker = String(row.ticker || "").toUpperCase();
    return (
      predictionMap.get(ticker) || {
        ticker,
        signal: "HOLD",
        label: "Neutral",
        confidence: 0,
        explanation: "No prediction data available for this holding yet."
      }
    );
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Portfolio Summary</h1>
      <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 rounded-2xl border border-[#263247] bg-[#172033] p-4 md:grid-cols-4">
        <Input placeholder="Ticker" value={form.ticker} onChange={(e) => setForm((p) => ({ ...p, ticker: e.target.value }))} />
        <Input type="number" step="0.01" placeholder="Quantity" value={form.quantity} onChange={(e) => setForm((p) => ({ ...p, quantity: e.target.value }))} />
        <Input type="number" step="0.01" placeholder="Invested Amount" value={form.investedAmount} onChange={(e) => setForm((p) => ({ ...p, investedAmount: e.target.value }))} />
        <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save Holding"}</Button>
      </form>

      <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4">
        <table className="w-full text-sm">
          <thead className="text-[#94A3B8]">
            <tr>
              <th className="py-2 text-left">Ticker</th>
              <th className="py-2 text-left">Quantity</th>
              <th className="py-2 text-left">Invested</th>
              <th className="py-2 text-left">Current Value</th>
              <th className="py-2 text-left">P/L</th>
            </tr>
          </thead>
          <tbody>
            {(portfolio.holdings || []).map((row) => (
              <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                <td className="py-3">{row.ticker}</td>
                <td className="py-3">{row.quantity}</td>
                <td className="py-3 font-mono">${Number(row.investedAmount).toFixed(2)}</td>
                <td className="py-3 font-mono">${Number(row.currentValue).toFixed(2)}</td>
                <td className={`py-3 ${Number(row.pnl) >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                  {Number(row.pnl) >= 0 ? "+" : ""}${Number(row.pnl).toFixed(2)} ({Number(row.pnlPct).toFixed(2)}%)
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-xs text-[#94A3B8]">
          Total Invested: ${Number(portfolio.summary?.totalInvested || 0).toFixed(2)} | Current Value: ${Number(
            portfolio.summary?.currentValue || 0
          ).toFixed(2)} | Portfolio P/L: {Number(portfolio.summary?.totalPnl || 0) >= 0 ? "+" : ""}${Number(
            portfolio.summary?.totalPnl || 0
          ).toFixed(2)} ({Number(portfolio.summary?.totalPnlPct || 0).toFixed(2)}%)
        </p>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Portfolio Prediction Cards</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {portfolioPredictions.map((prediction, idx) => (
            <PredictionCard key={`${prediction.ticker}-${idx}`} prediction={prediction} />
          ))}
        </div>
      </div>
    </div>
  );
}
