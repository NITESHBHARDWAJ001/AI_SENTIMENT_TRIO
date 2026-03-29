import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { FilterBar } from "../../components/common/FilterBar";
import { ModelStatusBadge } from "../../components/common/ModelStatusBadge";
import { SearchBar } from "../../components/common/SearchBar";
import { SentimentBadge } from "../../components/common/SentimentBadge";
import { cardReveal, pageStagger, sectionFadeUp } from "../../lib/motion";
import { getAllPredictions, predictRange } from "../../services/publicService";

export function PredictionsPage() {
  const [active, setActive] = useState("1M");
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [rangeResult, setRangeResult] = useState(null);
  const [rangeError, setRangeError] = useState("");
  const [form, setForm] = useState({
    ticker: "AAPL",
    company: "Apple Inc",
    start_date: "2025-01-01",
    range_days: "7"
  });

  useEffect(() => {
    getAllPredictions().then(setRows);
  }, []);

  const filtered = rows.filter((row) => row.ticker.toLowerCase().includes(query.toLowerCase()));

  const onRangePredict = async (e) => {
    e.preventDefault();
    setRangeError("");
    setSubmitting(true);
    try {
      const result = await predictRange({
        ticker: form.ticker,
        company: form.company,
        start_date: form.start_date,
        range_days: Number(form.range_days)
      });
      setRangeResult(result);
    } catch (error) {
      setRangeError(error.message);
      setRangeResult(null);
    }
    setSubmitting(false);
  };

  return (
    <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-4">
      <Motion.h1 variants={sectionFadeUp} className="text-2xl font-semibold">Predictions</Motion.h1>
      <Motion.div variants={cardReveal}><ModelStatusBadge /></Motion.div>
      <Motion.div variants={sectionFadeUp} className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h2 className="mb-3 text-base font-semibold">Predict by Company, Date, and Range</h2>
        <form onSubmit={onRangePredict} className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Input
            placeholder="Ticker (e.g. AAPL)"
            value={form.ticker}
            onChange={(e) => setForm((prev) => ({ ...prev, ticker: e.target.value }))}
          />
          <Input
            placeholder="Company Name"
            value={form.company}
            onChange={(e) => setForm((prev) => ({ ...prev, company: e.target.value }))}
          />
          <Input
            type="date"
            value={form.start_date}
            onChange={(e) => setForm((prev) => ({ ...prev, start_date: e.target.value }))}
          />
          <Input
            type="number"
            min="1"
            max="90"
            placeholder="Range in days"
            value={form.range_days}
            onChange={(e) => setForm((prev) => ({ ...prev, range_days: e.target.value }))}
          />
          <div className="md:col-span-4">
            <Button type="submit" disabled={submitting}>
              {submitting ? "Generating..." : "Generate Range Predictions"}
            </Button>
          </div>
        </form>

        {rangeError ? <p className="mt-3 text-sm text-[#FF5252]">{rangeError}</p> : null}

        {rangeResult ? (
          <Motion.div variants={cardReveal} className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold">
                {form.company || rangeResult.ticker} ({rangeResult.ticker})
              </p>
              <span className="text-xs text-[var(--text-muted)]">
                Source: {rangeResult.modelSource === "dumped_model" ? "Dumped .pkl model" : "Fallback model"}
              </span>
            </div>
            {rangeResult.modelSource !== "dumped_model" ? (
              <p className="mt-2 text-xs text-[#FFD166]">
                Backend is not currently using dumped model artifacts. Install backend dependencies and restart Flask.
              </p>
            ) : null}
            <div className="mt-3 overflow-hidden rounded-xl border border-[var(--border)]">
              <table className="w-full text-left text-sm">
                <thead className="bg-[var(--bg-main)] text-[var(--text-muted)]">
                  <tr>
                    <th className="p-2">Date</th>
                    <th className="p-2">Signal</th>
                    <th className="p-2">Label</th>
                    <th className="p-2">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {rangeResult.predictions?.map((item) => (
                    <tr key={`${item.date}-${item.ticker}`} className="interactive-row border-t border-[var(--border)]">
                      <td className="p-2 font-mono">{item.date}</td>
                      <td className="p-2">{item.signal}</td>
                      <td className="p-2"><SentimentBadge value={item.label} /></td>
                      <td className="p-2 font-mono text-[#58A6FF]">{item.confidence}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Motion.div>
        ) : null}
      </Motion.div>

      <Motion.div variants={sectionFadeUp} className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <SearchBar value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search prediction by ticker" />
        <FilterBar active={active} onChange={setActive} />
      </Motion.div>
      <Motion.div variants={sectionFadeUp} className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-card)]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[var(--bg-secondary)] text-[var(--text-muted)]">
            <tr>
              <th className="p-3">Ticker</th>
              <th className="p-3">Verdict</th>
              <th className="p-3">Label</th>
              <th className="p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                <td className="p-3 font-semibold">{row.ticker}</td>
                <td className="p-3 font-semibold">
                  <span className={row.signal === "BUY" ? "text-[#00C853]" : row.signal === "SELL" ? "text-[#FF5252]" : "text-[#FFD166]"}>
                    {row.signal || "HOLD"}
                  </span>
                </td>
                <td className="p-3"><SentimentBadge value={row.label} /></td>
                <td className="p-3 font-mono text-[#58A6FF]">{row.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Motion.div>
    </Motion.div>
  );
}
