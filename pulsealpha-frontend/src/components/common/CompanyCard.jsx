import { motion } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { SentimentBadge } from "./SentimentBadge";

export function CompanyCard({ company, onClick }) {
  const positive = company.change >= 0;
  const MotionButton = motion.button;

  return (
    <MotionButton
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
      className="w-full text-left"
      onClick={() => onClick?.(company.ticker)}
    >
      <Card className="h-full hover:border-[#3B82F6]/50">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-[#F9FAFB]">{company.ticker}</h4>
            <SentimentBadge value={company.sentimentLabel} />
          </div>
          <p className="line-clamp-1 text-sm text-[#94A3B8]">{company.name}</p>
          <div className="flex items-center justify-between">
            <span className="font-mono text-xl text-[#F9FAFB]">${company.price.toFixed(2)}</span>
            <span className={`inline-flex items-center gap-1 text-sm ${positive ? "text-[#10B981]" : "text-[#EF4444]"}`}>
              {positive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {company.change.toFixed(2)}%
            </span>
          </div>
        </CardContent>
      </Card>
    </MotionButton>
  );
}
