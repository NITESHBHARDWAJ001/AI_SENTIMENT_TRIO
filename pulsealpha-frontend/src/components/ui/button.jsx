import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#58A6FF] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[#58A6FF] text-[#0E1117] shadow-[0_8px_18px_rgba(88,166,255,0.32)] hover:bg-[#78B8FF]",
        secondary: "bg-[var(--bg-card)] text-[var(--text-main)] border border-[var(--border)] hover:border-[#58A6FF]/45 hover:bg-[#1A202A]",
        ghost: "text-[var(--text-muted)] hover:bg-[#1A202A] hover:text-[var(--text-main)]",
        danger: "bg-[#FF5252] text-[#0E1117] hover:bg-[#FF6B6B]"
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-5"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);

export function Button({ className, variant, size, ...props }) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
