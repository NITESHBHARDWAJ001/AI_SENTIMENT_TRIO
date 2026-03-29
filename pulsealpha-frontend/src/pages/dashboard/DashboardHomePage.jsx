import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { BellRing, Bookmark, Sparkles, TrendingUp } from "lucide-react";
import { AlertCard } from "../../components/common/AlertCard";
import { KpiCard } from "../../components/common/KpiCard";
import { NewsCard } from "../../components/common/NewsCard";
import { PredictionCard } from "../../components/common/PredictionCard";
import { WatchlistCard } from "../../components/common/WatchlistCard";
import { Button } from "../../components/ui/button";
import { cardReveal, pageStagger, sectionFadeUp, titleWords } from "../../lib/motion";
import { getDashboardData, getSavedNews } from "../../services/userService";

export function DashboardHomePage() {
  const [dashboard, setDashboard] = useState(null);
  const [news, setNews] = useState([]);
  const [mode, setMode] = useState("beginner");

  useEffect(() => {
    getDashboardData().then(setDashboard);
    getSavedNews().then(setNews);
  }, []);

  if (!dashboard) return null;

  const keyPrediction = (dashboard.predictions || []).sort((a, b) => Number(b.confidence || 0) - Number(a.confidence || 0))[0] || null;

  const welcomeWords = ["Welcome", "back,", dashboard.welcomeName || "Investor"];

  return (
    <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-6">
      <Motion.section variants={sectionFadeUp} className="rounded-2xl border border-[#58A6FF]/25 bg-gradient-to-r from-[var(--bg-card)] via-[var(--bg-secondary)] to-[#16202c] p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="flex flex-wrap gap-x-2 text-2xl font-semibold">
              {welcomeWords.map((word) => (
                <Motion.span key={word} variants={titleWords}>
                  {word}
                </Motion.span>
              ))}
            </h1>
            <Motion.p variants={sectionFadeUp} className="text-[var(--text-muted)]">
              Your personalized AI market intelligence feed is ready.
            </Motion.p>
          </div>
          <Motion.div variants={cardReveal} className="flex items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--bg-main)]/60 p-1">
            <Button size="sm" variant={mode === "beginner" ? "default" : "ghost"} onClick={() => setMode("beginner")}>Beginner</Button>
            <Button size="sm" variant={mode === "advanced" ? "default" : "ghost"} onClick={() => setMode("advanced")}>Advanced</Button>
          </Motion.div>
        </div>
      </Motion.section>

      <Motion.section variants={sectionFadeUp} className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Motion.div variants={cardReveal}><KpiCard label="Watchlist Sentiment" value={dashboard.kpis.watchlistSentiment} icon={TrendingUp} delta="Composite score" /></Motion.div>
        <Motion.div variants={cardReveal}><KpiCard label="Watchlist Performance" value={dashboard.kpis.watchlistPerformance} icon={TrendingUp} delta="Since open" sentiment="Positive" /></Motion.div>
        <Motion.div variants={cardReveal}><KpiCard label="Alerts Triggered" value={dashboard.kpis.alertsTriggered} icon={BellRing} delta="Today" /></Motion.div>
        <Motion.div variants={cardReveal}><KpiCard label="Saved Articles" value={dashboard.kpis.savedArticles} icon={Bookmark} delta="Knowledge base" /></Motion.div>
        <Motion.div variants={cardReveal}><KpiCard label="Strongest Prediction" value={dashboard.kpis.strongestPrediction} icon={Sparkles} delta="Model confidence" /></Motion.div>
      </Motion.section>

      <Motion.section variants={sectionFadeUp} className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">My Watchlist</h2>
          <Motion.div variants={pageStagger} initial="hidden" animate="show" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {dashboard.watchlist.map((item) => (
              <Motion.div key={item.ticker} variants={cardReveal}>
                <WatchlistCard item={item} />
              </Motion.div>
            ))}
          </Motion.div>
        </div>
        <Motion.div variants={cardReveal}>
          <PredictionCard prediction={keyPrediction} />
        </Motion.div>
      </Motion.section>

      <Motion.section variants={sectionFadeUp} className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Motion.div variants={cardReveal} className="xl:col-span-2 rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <h2 className="mb-3 text-lg font-semibold">My Portfolio (Invested Amount Personalization)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[var(--text-muted)]">
                <tr>
                  <th className="p-2">Ticker</th>
                  <th className="p-2">Qty</th>
                  <th className="p-2">Invested</th>
                  <th className="p-2">Current</th>
                  <th className="p-2">P/L</th>
                </tr>
              </thead>
              <tbody>
                {(dashboard.portfolio?.holdings || []).map((row) => (
                  <tr key={row.ticker} className="interactive-row border-t border-[var(--border)]">
                    <td className="p-2 font-semibold">{row.ticker}</td>
                    <td className="p-2">{row.quantity}</td>
                    <td className="p-2 font-mono">${Number(row.investedAmount).toFixed(2)}</td>
                    <td className="p-2 font-mono">${Number(row.currentValue).toFixed(2)}</td>
                    <td className={`p-2 font-mono ${Number(row.pnl) >= 0 ? "text-[#00C853]" : "text-[#FF5252]"}`}>
                      {Number(row.pnl) >= 0 ? "+" : ""}${Number(row.pnl).toFixed(2)} ({Number(row.pnlPct).toFixed(2)}%)
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-[var(--text-muted)]">
            Total Invested: ${Number(dashboard.portfolio?.summary?.totalInvested || 0).toFixed(2)} | Current Value: ${Number(
              dashboard.portfolio?.summary?.currentValue || 0
            ).toFixed(2)}
          </p>
        </Motion.div>

        <Motion.div variants={cardReveal} className="rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <h2 className="mb-3 text-lg font-semibold">Prediction Engine Module</h2>
          {mode === "beginner" ? (
            <div className="space-y-2 text-sm text-[var(--text-muted)]">
              <p>
                Beginner view explains signal quality in plain language so you can learn quickly.
              </p>
              <p>
                Top signal today: <span className="text-[var(--text-main)]">{dashboard.kpis.strongestPrediction}</span>
              </p>
              <p>
                Tip: Focus on confidence above 70% and cross-check with your invested holdings.
              </p>
            </div>
          ) : (
            <div className="space-y-2 text-sm">
              {(dashboard.predictions || []).slice(0, 5).map((row) => (
                <Motion.div key={row.ticker} variants={cardReveal} className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2">
                  <span className="font-semibold">{row.ticker}</span>
                  <span className="text-[var(--text-muted)]">{row.label}</span>
                  <span className="font-mono text-[#58A6FF]">{Number(row.confidence).toFixed(1)}%</span>
                </Motion.div>
              ))}
            </div>
          )}
        </Motion.div>
      </Motion.section>

      <Motion.section variants={sectionFadeUp} className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">Personalized News Feed</h2>
          <Motion.div variants={pageStagger} initial="hidden" animate="show" className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {news.map((item, idx) => (
              <Motion.div key={`${item.id ?? "news"}-${item.ticker ?? "market"}-${idx}`} variants={cardReveal}><NewsCard item={item} /></Motion.div>
            ))}
          </Motion.div>
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">My Alerts</h2>
          <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-3">
            {dashboard.alerts.map((item, idx) => (
              <Motion.div key={`${item.ticker}-${idx}`} variants={cardReveal}><AlertCard alert={item} /></Motion.div>
            ))}
          </Motion.div>
        </div>
      </Motion.section>
    </Motion.div>
  );
}
