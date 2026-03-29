import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { RouteTransition } from "../components/layout/RouteTransition";
import { Sidebar } from "../components/layout/Sidebar";

const links = [
  { to: "/", label: "Home" },
  { to: "/market", label: "Market" },
  { to: "/predictions", label: "Predictions" },
  { to: "/news", label: "News" },
  { to: "/about", label: "About" },
  { to: "/login", label: "Login" }
];

export function PublicLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#F9FAFB]">
      <Sidebar mode="public" mobileOpen={open} onClose={() => setOpen(false)} />
      <header className="sticky top-0 z-20 border-b border-cyan-400/20 bg-[#0B1220]/95 backdrop-blur lg:ml-72">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-4 lg:px-8">
          <button className="rounded-lg border border-[#263247] px-2 py-1 text-sm lg:hidden" onClick={() => setOpen(true)}>
            Menu
          </button>
          <Link to="/" className="neon-text text-sm font-semibold tracking-wide text-[#22D3EE]">
            PulseAlpha Public Terminal
          </Link>
          <nav className="hidden items-center gap-5 md:flex">
            {links.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `text-sm transition ${isActive ? "text-[#F9FAFB]" : "text-[#94A3B8] hover:text-[#F9FAFB]"}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-[1400px] p-4 lg:ml-72 lg:p-8">
        <RouteTransition />
      </main>
      <footer className="border-t border-cyan-400/20 bg-[#111827]/70 lg:ml-72">
        <div className="mx-auto max-w-[1400px] px-4 py-6 text-xs text-[#94A3B8] lg:px-8">
          Methodology: PulseAlpha blends real-time financial news sentiment with technical momentum features. Predictions are informational, not investment advice.
        </div>
      </footer>
    </div>
  );
}
