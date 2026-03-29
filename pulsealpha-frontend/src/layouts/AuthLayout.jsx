import { Link } from "react-router-dom";
import { RouteTransition } from "../components/layout/RouteTransition";

export function AuthLayout() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0B1220] px-4 py-10 text-[#F9FAFB]">
      <div className="pointer-events-none absolute -left-20 top-10 h-72 w-72 rounded-full bg-[#3B82F6]/20 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-72 w-72 rounded-full bg-[#06B6D4]/20 blur-3xl" />
      <div className="relative z-10 w-full max-w-md rounded-2xl border border-[#263247] bg-[#111827]/90 p-6 shadow-2xl backdrop-blur">
        <Link to="/" className="mb-6 block text-center text-xl font-semibold text-[#F9FAFB]">
          PulseAlpha
        </Link>
        <RouteTransition />
      </div>
    </div>
  );
}
