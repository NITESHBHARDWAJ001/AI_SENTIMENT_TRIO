import { Search } from "lucide-react";
import { Input } from "../ui/input";

export function SearchBar({ placeholder = "Search ticker, company, signal...", value, onChange }) {
  return (
    <div className="relative w-full md:max-w-sm">
      <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
      <Input className="pl-9" placeholder={placeholder} value={value} onChange={onChange} />
    </div>
  );
}
