import { useEffect, useState } from "react";
import { BrainCircuit, Database, FlaskConical } from "lucide-react";
import { getModelInfo } from "../../services/publicService";

export function AboutPage() {
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    getModelInfo().then(setModelInfo);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">About PulseAlpha</h1>
      <p className="max-w-3xl text-[#94A3B8]">
        PulseAlpha combines financial news intelligence with market time-series features to generate sentiment signals and prediction probabilities for tracked companies.
      </p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4">
          <FlaskConical className="mb-2 text-[#06B6D4]" />
          <h3 className="font-semibold">Flask Backend</h3>
          <p className="text-sm text-[#94A3B8]">REST APIs serving market, news, and prediction endpoints.</p>
        </div>
        <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4">
          <BrainCircuit className="mb-2 text-[#3B82F6]" />
          <h3 className="font-semibold">ML Pipelines</h3>
          <p className="text-sm text-[#94A3B8]">Pre-trained sentiment and stock prediction models are loaded server-side.</p>
        </div>
        <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4">
          <Database className="mb-2 text-[#10B981]" />
          <h3 className="font-semibold">Data Feeds</h3>
          <p className="text-sm text-[#94A3B8]">Aggregated RSS and market history transformed into feature-rich datasets.</p>
        </div>
      </div>
      {modelInfo ? (
        <div className="rounded-2xl border border-[#263247] bg-[#111827] p-4 text-sm text-[#94A3B8]">
          <p>Sentiment Model: {modelInfo.sentimentModel}</p>
          <p>Prediction Model: {modelInfo.predictionModel}</p>
          <p>Backend: {modelInfo.backend}</p>
        </div>
      ) : null}
    </div>
  );
}
