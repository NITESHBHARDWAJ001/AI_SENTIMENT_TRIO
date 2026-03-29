import { Clock3 } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { SentimentBadge } from "./SentimentBadge";
import { cardReveal } from "../../lib/motion";

export function NewsCard({ item }) {
  const MotionDiv = motion.div;

  return (
    <MotionDiv variants={cardReveal} whileHover={{ y: -4 }} transition={{ duration: 0.24 }}>
      <Card className="h-full hover:border-[#58A6FF]/45">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <SentimentBadge value={item.sentiment} />
            <span className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
              <Clock3 size={12} /> {item.publishedAt}
            </span>
          </div>
          <h4 className="line-clamp-2 text-sm font-semibold text-[var(--text-main)]">{item.title}</h4>
          <p className="line-clamp-2 text-sm text-[var(--text-muted)]">{item.summary}</p>
          <p className="text-xs text-[var(--text-muted)]">{item.source}</p>
        </CardContent>
      </Card>
    </MotionDiv>
  );
}
