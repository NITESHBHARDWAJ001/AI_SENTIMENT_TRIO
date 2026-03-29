import { cn } from "../../lib/utils";

export function Card({ className, ...props }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-[var(--border)] bg-[var(--bg-card)] shadow-[0_10px_28px_rgba(0,0,0,0.24)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[#58A6FF]/45 hover:shadow-[0_0_0_1px_rgba(88,166,255,0.22),0_12px_28px_rgba(0,0,0,0.3)]",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }) {
  return <div className={cn("p-5 pb-3", className)} {...props} />;
}

export function CardTitle({ className, ...props }) {
  return <h3 className={cn("text-sm font-semibold text-[var(--text-main)]", className)} {...props} />;
}

export function CardContent({ className, ...props }) {
  return <div className={cn("p-5 pt-0", className)} {...props} />;
}
