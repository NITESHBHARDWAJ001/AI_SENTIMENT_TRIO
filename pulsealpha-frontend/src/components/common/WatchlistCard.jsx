import { Star } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { SentimentBadge } from "./SentimentBadge";
import { cardReveal } from "../../lib/motion";

export function WatchlistCard({ item }) {
  const MotionDiv = motion.div;

  return (
    <MotionDiv variants={cardReveal} whileHover={{ y: -4 }} transition={{ duration: 0.24 }}>
      <Card className="hover:border-[#58A6FF]/45">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <h4 className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--text-main)]">
              <Star size={14} className="text-[#FFD166]" /> {item.ticker}
            </h4>
            <SentimentBadge value={item.sentiment} />
          </div>
          <div className="flex items-center justify-between">
            <p className="font-mono text-xl text-[var(--text-main)]">${item.price.toFixed(2)}</p>
            <p className={item.change >= 0 ? "text-[#00C853]" : "text-[#FF5252]"}>{item.change.toFixed(2)}%</p>
          </div>
          <div className="space-y-2">
            <p className="text-xs text-[var(--text-muted)]">{item.latestNewsMessage || "No latest news status"}</p>
            <p className={`text-xs font-medium ${item.hasLatestHourReport ? "text-[#00C853]" : "text-[#FFD166]"}`}>
              {item.hasLatestHourReport ? "Latest 1-hour report available" : "Latest report older than 1 hour"}
            </p>
          </div>
        </CardContent>
      </Card>
    </MotionDiv>
  );
}
