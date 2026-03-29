import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
  {
    variants: {
      variant: {
        positive: "border-[#00C853]/40 bg-[#00C853]/12 text-[#00C853]",
        negative: "border-[#FF5252]/40 bg-[#FF5252]/12 text-[#FF5252]",
        neutral: "border-[#FFD166]/40 bg-[#FFD166]/12 text-[#FFD166]",
        info: "border-[#58A6FF]/40 bg-[#58A6FF]/12 text-[#58A6FF]"
      }
    },
    defaultVariants: {
      variant: "info"
    }
  }
);

export function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export default Badge;
