import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Navbar } from "../components/layout/Navbar";
import { RouteTransition } from "../components/layout/RouteTransition";
import { Sidebar } from "../components/layout/Sidebar";
import { useAuth } from "../contexts/useAuth";

export function DashboardLayout() {
  const [open, setOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#F9FAFB]">
      <Sidebar mobileOpen={open} onClose={() => setOpen(false)} />
      <div className="lg:ml-72">
        <Navbar onOpenSidebar={() => setOpen(true)} title="PulseAlpha Personal Terminal" />
        <main className="p-4 lg:p-6">
          <RouteTransition />
        </main>
      </div>
    </div>
  );
}
