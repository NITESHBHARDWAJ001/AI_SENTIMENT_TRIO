import { Bell, Menu, UserCircle2 } from "lucide-react";
import { SearchBar } from "../common/SearchBar";

export function Navbar({ onOpenSidebar, title = "PulseAlpha Terminal" }) {
  return (
    <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[var(--bg-main)]/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-3 px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] lg:hidden"
            onClick={onOpenSidebar}
          >
            <Menu size={18} />
          </button>
          <div>
            <p className="text-sm font-semibold text-[var(--text-main)]">{title}</p>
            <p className="text-xs text-[var(--text-muted)]">AI stock sentiment and prediction intelligence</p>
          </div>
        </div>
        <div className="hidden flex-1 justify-center md:flex">
          <SearchBar />
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-[var(--text-main)]">
            <Bell size={16} />
          </button>
          <button className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-[var(--text-main)]">
            <UserCircle2 size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
