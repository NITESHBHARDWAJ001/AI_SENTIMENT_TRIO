import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { Badge } from "../ui/badge";

export function SentimentBadge({ value = "Neutral" }) {
  const normalized = value.toLowerCase();

  if (normalized.includes("bull") || normalized.includes("positive")) {
    return (
      <Badge variant="positive" className="gap-1">
        <ArrowUpRight size={12} /> Positive
      </Badge>
    );
  }

  if (normalized.includes("bear") || normalized.includes("negative")) {
    return (
      <Badge variant="negative" className="gap-1">
        <ArrowDownRight size={12} /> Negative
      </Badge>
    );
  }

  return (
    <Badge variant="neutral" className="gap-1">
      <ArrowRight size={12} /> Neutral
    </Badge>
  );
}
