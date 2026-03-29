import { Bell } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { cardReveal, gentleFloat } from "../../lib/motion";

export function AlertCard({ alert }) {
  const MotionDiv = motion.div;

  return (
    <MotionDiv variants={cardReveal} whileHover={{ y: -3 }} transition={{ duration: 0.24 }}>
      <Card className="border-l-4 border-l-[#58A6FF]">
        <CardContent className="space-y-2 p-4">
          <div className="flex items-center justify-between">
            <p className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--text-main)]">
              <motion.span animate={gentleFloat}>
                <Bell size={14} className="text-[#58A6FF]" />
              </motion.span>
              {alert.ticker}
            </p>
            <span className="text-xs text-[var(--text-muted)]">{alert.time}</span>
          </div>
          <p className="text-sm text-[var(--text-muted)]">{alert.message}</p>
        </CardContent>
      </Card>
    </MotionDiv>
  );
}
