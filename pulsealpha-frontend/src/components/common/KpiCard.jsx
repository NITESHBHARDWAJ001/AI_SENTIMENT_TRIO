import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { AnimatedCounter } from "./AnimatedCounter";
import { SentimentBadge } from "./SentimentBadge";

export function KpiCard({ label, value, icon: Icon, delta, sentiment, mono = false }) {
  const numeric = typeof value === "number";
  const MotionDiv = motion.div;

  return (
    <MotionDiv whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
      <Card className="h-full">
        <CardContent className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-[#94A3B8]">{label}</p>
            {Icon ? <Icon size={16} className="text-[#06B6D4]" /> : null}
          </div>
          <div className={`text-2xl font-semibold text-[#F9FAFB] ${mono ? "font-mono" : ""}`}>
            {numeric ? <AnimatedCounter value={value} decimals={value % 1 !== 0 ? 2 : 0} /> : value}
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-[#94A3B8]">{delta}</span>
            {sentiment ? <SentimentBadge value={sentiment} /> : null}
          </div>
        </CardContent>
      </Card>
    </MotionDiv>
  );
}
