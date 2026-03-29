import { useEffect, useState } from "react";
import { BadgeCheck, CircleAlert, LoaderCircle } from "lucide-react";
import { getModelInfo } from "../../services/publicService";

export function ModelStatusBadge({ compact = false }) {
  const [loading, setLoading] = useState(true);
  const [info, setInfo] = useState(null);

  useEffect(() => {
    getModelInfo()
      .then((data) => setInfo(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="inline-flex items-center gap-2 rounded-xl border border-[#263247] bg-[#111827] px-3 py-1.5 text-xs text-[#94A3B8]">
        <LoaderCircle size={14} className="animate-spin" /> Checking model
      </div>
    );
  }

  const loaded = Boolean(info?.modelLoaded);

  if (compact) {
    return (
      <div
        className={`inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs ${
          loaded
            ? "border-emerald-400/30 bg-emerald-500/10 text-[#10B981]"
            : "border-amber-400/30 bg-amber-500/10 text-[#F59E0B]"
        }`}
      >
        {loaded ? <BadgeCheck size={14} /> : <CircleAlert size={14} />}
        {loaded ? "Dumped model active" : "Fallback active"}
      </div>
    );
  }

  return (
    <div
      className={`rounded-2xl border p-3 text-sm ${
        loaded
          ? "border-emerald-400/30 bg-emerald-500/10 text-[#10B981]"
          : "border-amber-400/30 bg-amber-500/10 text-[#F59E0B]"
      }`}
    >
      <div className="flex items-center gap-2 font-semibold">
        {loaded ? <BadgeCheck size={16} /> : <CircleAlert size={16} />}
        {loaded ? "Prediction Engine: Dumped Model" : "Prediction Engine: Fallback"}
      </div>
      <p className="mt-1 text-xs text-[#94A3B8]">
        {loaded
          ? `Using ${info?.predictionModel || "data/xgboost_model.pkl"}`
          : info?.loadError || "Model not loaded in current runtime. Install xgboost in backend env."}
      </p>
    </div>
  );
}
