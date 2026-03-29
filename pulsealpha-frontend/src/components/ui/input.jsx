import { cn } from "../../lib/utils";

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--bg-card)] px-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-muted)] focus:border-[#58A6FF]",
        className
      )}
      {...props}
    />
  );
}
