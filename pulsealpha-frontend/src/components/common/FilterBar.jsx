import { SlidersHorizontal } from "lucide-react";

const intervals = ["1D", "1W", "1M", "3M", "1Y"];

export function FilterBar({ active = "1M", onChange }) {
  return (
    <div className="sticky top-16 z-20 flex items-center gap-2 rounded-xl border border-[#263247] bg-[#111827]/95 p-2 backdrop-blur md:w-fit">
      <span className="inline-flex items-center gap-2 px-2 text-xs text-[#94A3B8]">
        <SlidersHorizontal size={14} /> Range
      </span>
      {intervals.map((item) => (
        <button
          key={item}
          onClick={() => onChange?.(item)}
          className={`rounded-lg px-3 py-1.5 text-xs transition ${
            active === item ? "bg-[#3B82F6] text-white" : "text-[#94A3B8] hover:bg-[#172033]"
          }`}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
