import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, BarChart3, Newspaper, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import { ChartCard } from "../../components/common/ChartCard";
import { CompanyCard } from "../../components/common/CompanyCard";
import { KpiCard } from "../../components/common/KpiCard";
import { LoadingSkeleton } from "../../components/common/LoadingSkeleton";
import { NewsCard } from "../../components/common/NewsCard";
import { PredictionCard } from "../../components/common/PredictionCard";
import { ModelStatusBadge } from "../../components/common/ModelStatusBadge";
import { PriceChart } from "../../components/charts/PriceChart";
import { OverlayChart } from "../../components/charts/OverlayChart";
import { SentimentChart } from "../../components/charts/SentimentChart";
import { Button } from "../../components/ui/button";
import { getOverview } from "../../services/publicService";

export function HomePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const MotionSection = motion.section;
  const MotionDiv = motion.div;

  const staggerContainer = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.06
      }
    }
  };

  const fadeUp = {
    hidden: { opacity: 0, y: 14 },
    show: { opacity: 1, y: 0, transition: { duration: 0.28 } }
  };

  useEffect(() => {
    getOverview().then((data) => {
      setOverview(data);
      setLoading(false);
    });
  }, []);

  if (loading || !overview) {
    return <LoadingSkeleton />;
  }

  const { overviewStats, companies, chartSeries, latestNews, predictionSnapshot, topMovers } = overview;
  const safePrediction = predictionSnapshot || {
    ticker: "N/A",
    label: "Neutral",
    confidence: 0,
    explanation: "No prediction data available."
  };

  return (
    <div className="space-y-6">
      <MotionSection
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="neon-glow rounded-2xl border border-[#58A6FF]/25 bg-gradient-to-r from-[var(--bg-card)] via-[var(--bg-secondary)] to-[#16202c] p-6"
      >
        <h1 className="neon-text text-3xl font-semibold">PulseAlpha</h1>
        <p className="mt-2 max-w-2xl text-[var(--text-muted)]">
          AI-powered stock sentiment and prediction intelligence for modern investors.
        </p>
        <div className="mt-3">
          <ModelStatusBadge compact />
        </div>
        <div className="mt-4 flex gap-3">
          <Button onClick={() => navigate("/market")}>View Market</Button>
          <Button variant="secondary" onClick={() => navigate("/login")}>Open Personal Dashboard</Button>
        </div>
      </MotionSection>

      <MotionDiv
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5"
      >
        <motion.div variants={fadeUp}><KpiCard label="Total Articles Analyzed" value={overviewStats.totalArticles.toLocaleString()} icon={Newspaper} delta="24h rolling" mono /></motion.div>
        <motion.div variants={fadeUp}><KpiCard label="Companies Tracked" value={overviewStats.companiesTracked} icon={BarChart3} delta="Live universe" /></motion.div>
        <motion.div variants={fadeUp}><KpiCard label="Avg Market Sentiment" value={overviewStats.avgSentiment} icon={Activity} delta="Scale: -1 to +1" /></motion.div>
        <motion.div variants={fadeUp}><KpiCard label="Top Bullish Stock" value={overviewStats.topBullish} icon={TrendingUp} delta="Momentum + sentiment" sentiment="Positive" /></motion.div>
        <motion.div variants={fadeUp}><KpiCard label="Top Bearish Stock" value={overviewStats.topBearish} icon={TrendingUp} delta="Negative pressure" sentiment="Negative" /></motion.div>
      </MotionDiv>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Tracked Companies</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {companies.map((company) => (
            <CompanyCard key={company.ticker} company={company} onClick={(ticker) => navigate(`/company/${ticker}`)} />
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard title="Sentiment Trend" className="xl:col-span-2">
          <SentimentChart data={chartSeries} />
        </ChartCard>
        <PredictionCard prediction={safePrediction} />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Price Trend">
          <PriceChart data={chartSeries} />
        </ChartCard>
        <ChartCard title="Price vs Sentiment Overlay">
          <OverlayChart data={chartSeries} />
        </ChartCard>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">Latest News</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {latestNews.map((item) => (
              <NewsCard key={item.id} item={item} />
            ))}
          </div>
        </div>
        <div>
          <h2 className="mb-3 text-lg font-semibold">Top Movers</h2>
          <div className="space-y-3 rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4">
            {topMovers.map((mover) => (
              <div key={mover.ticker} className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{mover.ticker}</p>
                  <p className="font-mono text-[#58A6FF]">{mover.move}</p>
                </div>
                <p className="text-sm text-[var(--text-muted)]">{mover.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
