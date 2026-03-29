import { useEffect, useState } from "react";
import { motion as Motion } from "framer-motion";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { FilterBar } from "../../components/common/FilterBar";
import { NewsCard } from "../../components/common/NewsCard";
import { SearchBar } from "../../components/common/SearchBar";
import { cardReveal, pageStagger, sectionFadeUp } from "../../lib/motion";
import { getNewsFeed, ingestNews } from "../../services/publicService";

export function NewsFeedPage() {
  const [active, setActive] = useState("1W");
  const [query, setQuery] = useState("");
  const [news, setNews] = useState([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ ticker: "", company: "", title: "", summary: "", source: "", sentiment: "Neutral" });

  useEffect(() => {
    getNewsFeed().then(setNews);
  }, []);

  const onIngest = async (e) => {
    e.preventDefault();
    setSaving(true);
    await ingestNews(form);
    const updated = await getNewsFeed();
    setNews(updated);
    setForm({ ticker: "", company: "", title: "", summary: "", source: "", sentiment: "Neutral" });
    setSaving(false);
  };

  const filtered = news.filter((item) => item.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <Motion.div variants={pageStagger} initial="hidden" animate="show" className="space-y-4">
      <Motion.h1 variants={sectionFadeUp} className="text-2xl font-semibold">News Feed</Motion.h1>
      <Motion.form variants={sectionFadeUp} onSubmit={onIngest} className="grid grid-cols-1 gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] p-4 md:grid-cols-3">
        <Input placeholder="Ticker" value={form.ticker} onChange={(e) => setForm((p) => ({ ...p, ticker: e.target.value }))} />
        <Input placeholder="Company" value={form.company} onChange={(e) => setForm((p) => ({ ...p, company: e.target.value }))} />
        <Input placeholder="Source" value={form.source} onChange={(e) => setForm((p) => ({ ...p, source: e.target.value }))} />
        <Input placeholder="Headline title" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} className="md:col-span-3" />
        <Input placeholder="Summary" value={form.summary} onChange={(e) => setForm((p) => ({ ...p, summary: e.target.value }))} className="md:col-span-2" />
        <Input placeholder="Sentiment (Positive/Negative/Neutral)" value={form.sentiment} onChange={(e) => setForm((p) => ({ ...p, sentiment: e.target.value }))} />
        <div className="md:col-span-3">
          <Button type="submit" disabled={saving}>{saving ? "Storing..." : "Store Realtime News in SQLite"}</Button>
        </div>
      </Motion.form>

      <Motion.div variants={sectionFadeUp} className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <SearchBar value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search headlines" />
        <FilterBar active={active} onChange={setActive} />
      </Motion.div>
      <Motion.div variants={sectionFadeUp} className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((item) => (
          <Motion.div key={item.id} variants={cardReveal}>
            <NewsCard item={item} />
          </Motion.div>
        ))}
      </Motion.div>
    </Motion.div>
  );
}
