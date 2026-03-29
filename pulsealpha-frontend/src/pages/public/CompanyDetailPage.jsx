import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { useParams } from "react-router-dom";
import { ChartCard } from "../../components/common/ChartCard";
import { NewsCard } from "../../components/common/NewsCard";
import { PredictionCard } from "../../components/common/PredictionCard";
import { TechnicalIndicatorCard } from "../../components/common/TechnicalIndicatorCard";
import { SentimentBadge } from "../../components/common/SentimentBadge";
import { OverlayChart } from "../../components/charts/OverlayChart";
import { PriceChart } from "../../components/charts/PriceChart";
import { ScoreBreakdownChart } from "../../components/charts/ScoreBreakdownChart";
import { SentimentChart } from "../../components/charts/SentimentChart";
import { cardReveal, pageStagger, sectionFadeUp } from "../../lib/motion";
import { getAllPredictions, getCompanyDetail } from "../../services/publicService";

export function CompanyDetailPage() {
  const { ticker = "AAPL" } = useParams();
  const [data, setData] = useState(null);
  const [summaryRows, setSummaryRows] = useState([]);

  useEffect(() => {
    getCompanyDetail(ticker).then(setData);
    getAllPredictions().then(setSummaryRows);
  }, [ticker]);

  if (!data) return null;

  const { company, news, sentimentSeries, prediction } = data;
  const safeCompany = company || {
    name: ticker,
    ticker,
    price: 0,
    sentimentLabel: "Neutral"
  };
  const safePrediction = prediction || {};
  const safeNews = Array.isArray(news) ? news : [];
  const safeSeries = Array.isArray(sentimentSeries) ? sentimentSeries : [];

  return (
    <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-6">
      <section className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-[var(--text-main)]">{safeCompany.name}</h1>
            <p className="text-[var(--text-muted)]">{safeCompany.ticker}</p>
          </div>
          <div className="flex items-center gap-4">
            <p className="font-mono text-3xl">${Number(safeCompany.price || 0).toFixed(2)}</p>
            <SentimentBadge value={safeCompany.sentimentLabel} />
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Signal</p>
          <p className="mt-2 text-3xl font-bold text-[var(--text-main)]">{safePrediction.signal || "HOLD"}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Final Score</p>
          <p className="mt-2 font-mono text-3xl text-[var(--text-main)]">{Number(safePrediction.final_score || 0).toFixed(3)}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Confidence</p>
          <p className="mt-2 font-mono text-3xl text-[var(--text-main)]">{Number(safePrediction.confidence_pct || safePrediction.confidence || 0).toFixed(1)}%</p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Last Close</p>
          <p className="mt-2 font-mono text-3xl text-[var(--text-main)]">${Number(safePrediction.close || safeCompany.price || 0).toFixed(2)}</p>
        </div>
      </section>

      <section className="rounded-2xl border border-[#58A6FF]/35 bg-[#58A6FF]/10 p-4 text-sm text-[var(--text-main)]">
        {safePrediction.explanation || "No explanation available."}
      </section>

      <Motion.section variants={sectionFadeUp} className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-[var(--text-main)]">Advanced Analysis Studio</h2>
          <p className="text-xs text-[var(--text-muted)]">Price, sentiment, model and technicals in one visual section</p>
        </div>

        <Motion.div variants={pageStagger} initial="hidden" animate="show" className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Motion.div variants={cardReveal}>
            <ChartCard title="Main Stock Price Chart">
              <PriceChart data={safeSeries} />
            </ChartCard>
          </Motion.div>
          <Motion.div variants={cardReveal}>
            <ChartCard title="Sentiment Score Over Time">
              <SentimentChart data={safeSeries} showThresholds />
            </ChartCard>
          </Motion.div>
          <Motion.div variants={cardReveal}>
            <ChartCard title="Price vs Sentiment Overlay">
              <OverlayChart data={safeSeries} />
            </ChartCard>
          </Motion.div>
          <Motion.div variants={cardReveal}>
            <ChartCard title="Model Score Breakdown">
              <ScoreBreakdownChart prediction={safePrediction} />
            </ChartCard>
          </Motion.div>
        </Motion.div>

        <Motion.div variants={cardReveal} className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)]/60 p-3 text-xs text-[var(--text-muted)]">
          Analysis summary: combine trend direction (price), sentiment momentum, and model confidence before acting. Use this panel as your primary visual decision area.
        </Motion.div>
      </Motion.section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm text-[var(--text-muted)]">
          Use the Advanced Analysis Studio above for the full visual view, then use this prediction card for a quick final verdict check.
        </div>
        <PredictionCard prediction={safePrediction} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TechnicalIndicatorCard ticker={ticker} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="All Stocks - Signal Summary">
          <div className="max-h-72 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[var(--text-muted)]">
                <tr>
                  <th className="p-2">Ticker</th>
                  <th className="p-2">Signal</th>
                  <th className="p-2">Score</th>
                  <th className="p-2">Confidence</th>
                  <th className="p-2">Close</th>
                </tr>
              </thead>
              <tbody>
                {summaryRows.map((row) => (
                  <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                    <td className="p-2 font-semibold">{row.ticker}</td>
                    <td className="p-2">{row.signal || row.label || "N/A"}</td>
                    <td className="p-2 font-mono">{Number(row.score || 0).toFixed(3)}</td>
                    <td className="p-2 font-mono">{Number(row.confidence_pct || row.confidence || 0).toFixed(1)}%</td>
                    <td className="p-2 font-mono">${Number(row.close || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>

      <section className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm text-[var(--text-muted)]">
        Mini Explanation: Recent positive sentiment and momentum indicate moderate bullish outlook.
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Latest Related News</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {safeNews.map((item, idx) => (
            <NewsCard key={`${item.id ?? "news"}-${item.ticker ?? ticker}-${idx}`} item={item} />
          ))}
        </div>
      </section>
    </Motion.div>
  );
}
