import { Inbox } from "lucide-react";

export function EmptyState({ title = "No data yet", description = "Try adjusting filters or check back soon." }) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-2xl border border-dashed border-[#334155] bg-[#111827]/60 p-8 text-center">
      <Inbox className="mb-3 text-[#64748B]" />
      <h3 className="text-base font-semibold text-[#F9FAFB]">{title}</h3>
      <p className="mt-1 text-sm text-[#94A3B8]">{description}</p>
    </div>
  );
}
