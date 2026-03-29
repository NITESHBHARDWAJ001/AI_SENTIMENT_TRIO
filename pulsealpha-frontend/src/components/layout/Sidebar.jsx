import { NavLink } from "react-router-dom";
import {
  Bell,
  Bookmark,
  BriefcaseBusiness,
  Gauge,
  Home,
  LineChart,
  Newspaper,
  Settings,
  ShieldClose,
  Star
} from "lucide-react";

const publicLinks = [
  { to: "/", label: "Home", icon: Home },
  { to: "/market", label: "Market Overview", icon: LineChart },
  { to: "/predictions", label: "Predictions", icon: Gauge },
  { to: "/news", label: "News Feed", icon: Newspaper },
  { to: "/about", label: "About", icon: ShieldClose }
];

const privateLinks = [
  { to: "/app", label: "Dashboard Home", icon: Home },
  { to: "/app/watchlist", label: "Watchlist", icon: Star },
  { to: "/app/alerts", label: "Alerts", icon: Bell },
  { to: "/app/saved-news", label: "Saved News", icon: Bookmark },
  { to: "/app/portfolio", label: "Portfolio", icon: BriefcaseBusiness },
  { to: "/app/settings", label: "Settings", icon: Settings }
];

function SidebarLinks({ items, onNavigate }) {
  return (
    <nav className="space-y-1">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
              isActive
                ? "bg-[#58A6FF]/16 text-[var(--text-main)] shadow-[0_0_0_1px_rgba(88,166,255,0.25)]"
                : "text-[var(--text-muted)] hover:bg-[var(--bg-card)] hover:text-[var(--text-main)]"
            }`
          }
        >
          <item.icon size={15} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export function Sidebar({ mode = "private", mobileOpen = false, onClose }) {
  const links = mode === "public" ? publicLinks : privateLinks;

  return (
    <>
      {mobileOpen ? <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={onClose} /> : null}
      <aside
        className={`fixed left-0 top-0 z-50 h-full w-[82vw] max-w-72 border-r border-[var(--border)] bg-[var(--bg-secondary)]/95 p-4 shadow-[0_18px_36px_rgba(0,0,0,0.32)] transition-transform duration-300 lg:sticky lg:top-0 lg:z-20 lg:h-screen lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-6 border-b border-[var(--border)] pb-4">
          <h1 className="text-lg font-semibold text-[var(--text-main)]">PulseAlpha</h1>
          <p className="text-xs text-[var(--text-muted)]">Bloomberg-lite AI terminal</p>
        </div>
        <SidebarLinks items={links} onNavigate={onClose} />
      </aside>
    </>
  );
}
