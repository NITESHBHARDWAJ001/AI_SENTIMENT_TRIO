import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { ChartCard } from "../../components/common/ChartCard";
import { KpiCard } from "../../components/common/KpiCard";
import { OverlayChart } from "../../components/charts/OverlayChart";
import { SentimentChart } from "../../components/charts/SentimentChart";
import { cardReveal, pageStagger, sectionFadeUp } from "../../lib/motion";
import { getMarketSummary, getOverview, searchStocks } from "../../services/publicService";

export function MarketOverviewPage() {
  const [data, setData] = useState(null);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({ minSentiment: "-1", maxSentiment: "1" });
  const [searchResult, setSearchResult] = useState({ count: 0, results: [] });

  useEffect(() => {
    Promise.all([getOverview(), getMarketSummary()]).then(([overview, summary]) => setData({ overview, summary }));
    searchStocks({ includePrediction: true, limit: 20 }).then(setSearchResult);
  }, []);

  const runSearch = async () => {
    const result = await searchStocks({
      q: query,
      minSentiment: Number(filters.minSentiment),
      maxSentiment: Number(filters.maxSentiment),
      includePrediction: true,
      limit: 20
    });
    setSearchResult(result);
  };

  if (!data) return null;

  return (
    <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-6">
      <Motion.h1 variants={sectionFadeUp} className="text-2xl font-semibold">Market Overview</Motion.h1>
      <Motion.div variants={sectionFadeUp} className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.summary.sectors.map((sector) => (
          <Motion.div key={sector.name} variants={cardReveal}>
            <KpiCard
              label={sector.name}
              value={sector.sentiment.toFixed(2)}
              delta="Sector sentiment"
              sentiment={sector.sentiment > 0.6 ? "Positive" : sector.sentiment < 0.4 ? "Negative" : "Neutral"}
            />
          </Motion.div>
        ))}
      </Motion.div>
      <Motion.div variants={sectionFadeUp} className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Market Sentiment Arc">
          <SentimentChart data={data.overview.chartSeries} />
        </ChartCard>
        <ChartCard title="Cross Signal Overlay">
          <OverlayChart data={data.overview.chartSeries} />
        </ChartCard>
      </Motion.div>

      <Motion.div variants={sectionFadeUp} className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <h2 className="mb-3 text-lg font-semibold">Stock Search & Screener</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Input placeholder="Search ticker/company" value={query} onChange={(e) => setQuery(e.target.value)} />
          <Input type="number" step="0.01" placeholder="Min sentiment" value={filters.minSentiment} onChange={(e) => setFilters((p) => ({ ...p, minSentiment: e.target.value }))} />
          <Input type="number" step="0.01" placeholder="Max sentiment" value={filters.maxSentiment} onChange={(e) => setFilters((p) => ({ ...p, maxSentiment: e.target.value }))} />
          <Button onClick={runSearch}>Search</Button>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-[var(--text-muted)]">
              <tr>
                <th className="p-2">Ticker</th>
                <th className="p-2">Company</th>
                <th className="p-2">Price</th>
                <th className="p-2">Sentiment</th>
                <th className="p-2">Prediction</th>
              </tr>
            </thead>
            <tbody>
              {(searchResult.results || []).map((row) => (
                <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                  <td className="p-2 font-semibold">{row.ticker}</td>
                  <td className="p-2">{row.name}</td>
                  <td className="p-2 font-mono">${Number(row.price || 0).toFixed(2)}</td>
                  <td className="p-2">{row.sentimentLabel}</td>
                  <td className="p-2">
                    {row.prediction
                      ? `${row.prediction.signal || "HOLD"} (${Number(row.prediction.confidence).toFixed(1)}%)`
                      : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Motion.div>
    </Motion.div>
  );
}
