import { useEffect, useState } from "react";
import { PredictionCard } from "../../components/common/PredictionCard";
import { WatchlistCard } from "../../components/common/WatchlistCard";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { getDashboardData, getWatchlistProgress, removeWatchlist, upsertWatchlist } from "../../services/userService";

export function WatchlistPage() {
  const [rows, setRows] = useState([]);
  const [progress, setProgress] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [form, setForm] = useState({ ticker: "", targetBuyPrice: "", notes: "" });

  const load = async () => {
    const [dash, prog] = await Promise.all([getDashboardData(), getWatchlistProgress()]);
    setRows(dash.watchlist || []);
    setProgress(prog || []);
    setPredictions(dash.predictions || []);
  };

  useEffect(() => {
    let mounted = true;
    Promise.all([getDashboardData(), getWatchlistProgress()]).then(([dash, prog]) => {
      if (mounted) {
        setRows(dash.watchlist || []);
        setProgress(prog || []);
        setPredictions(dash.predictions || []);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  const onSave = async (e) => {
    e.preventDefault();
    await upsertWatchlist({
      ticker: form.ticker,
      targetBuyPrice: form.targetBuyPrice ? Number(form.targetBuyPrice) : null,
      notes: form.notes
    });
    setForm({ ticker: "", targetBuyPrice: "", notes: "" });
    await load();
  };

  const onRemove = async (ticker) => {
    await removeWatchlist(ticker);
    await load();
  };

  const predictionMap = new Map((predictions || []).map((row) => [String(row.ticker || "").toUpperCase(), row]));
  const watchlistPredictions = (rows || []).map((row) => {
    const ticker = String(row.ticker || "").toUpperCase();
    return (
      predictionMap.get(ticker) || {
        ticker,
        signal: "HOLD",
        label: "Neutral",
        confidence: 0,
        explanation: "No prediction data available for this watchlist stock yet."
      }
    );
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Watchlist</h1>
      <form onSubmit={onSave} className="grid grid-cols-1 gap-3 rounded-2xl border border-[#263247] bg-[#172033] p-4 md:grid-cols-4">
        <Input placeholder="Ticker" value={form.ticker} onChange={(e) => setForm((p) => ({ ...p, ticker: e.target.value }))} />
        <Input
          type="number"
          step="0.01"
          placeholder="Target Buy Price"
          value={form.targetBuyPrice}
          onChange={(e) => setForm((p) => ({ ...p, targetBuyPrice: e.target.value }))}
        />
        <Input placeholder="Notes" value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} />
        <Button type="submit">Save Watch Item</Button>
      </form>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((item) => (
          <div key={item.ticker} className="space-y-2">
            <WatchlistCard item={item} />
            <Button size="sm" variant="danger" onClick={() => onRemove(item.ticker)}>Remove</Button>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4">
        <h2 className="mb-3 text-lg font-semibold">Buy Progress Insights</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-[#94A3B8]">
              <tr>
                <th className="p-2">Ticker</th>
                <th className="p-2">Current</th>
                <th className="p-2">Target Buy</th>
                <th className="p-2">Distance</th>
                <th className="p-2">Buy Zone</th>
              </tr>
            </thead>
            <tbody>
              {progress.map((row) => (
                <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                  <td className="p-2 font-semibold">{row.ticker}</td>
                  <td className="p-2 font-mono">${Number(row.currentPrice || 0).toFixed(2)}</td>
                  <td className="p-2 font-mono">{row.targetBuyPrice ? `$${Number(row.targetBuyPrice).toFixed(2)}` : "Not set"}</td>
                  <td className="p-2">{row.distanceToTarget == null ? "N/A" : `${row.distanceToTarget >= 0 ? "+" : ""}$${Number(row.distanceToTarget).toFixed(2)}`}</td>
                  <td className={`p-2 ${row.buyZone ? "text-[#10B981]" : "text-[#F59E0B]"}`}>{row.buyZone ? "Yes" : "Watch"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Watchlist Prediction Cards</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {watchlistPredictions.map((prediction, idx) => (
            <PredictionCard key={`${prediction.ticker}-${idx}`} prediction={prediction} />
          ))}
        </div>
      </div>
    </div>
  );
}
