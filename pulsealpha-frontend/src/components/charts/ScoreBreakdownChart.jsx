import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const colorFor = (value) => {
  if (value > 0.05) return "#16A34A";
  if (value < -0.05) return "#DC2626";
  return "#D97706";
};

export function ScoreBreakdownChart({ prediction }) {
  const data = [
    { name: "Sentiment (60%)", value: Number(prediction?.sentiment_component || 0) },
    { name: "Returns (25%)", value: Number(prediction?.returns_component || 0) },
    { name: "Momentum (15%)", value: Number(prediction?.momentum_component || 0) }
  ];

  return (
    <div className="h-72 min-h-[260px] w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%" minWidth={280}>
        <BarChart data={data}>
          <CartesianGrid stroke="#263247" strokeDasharray="3 3" />
          <XAxis dataKey="name" stroke="#94A3B8" tickLine={false} axisLine={false} />
          <YAxis stroke="#94A3B8" tickLine={false} axisLine={false} domain={[-0.5, 0.5]} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #263247" }} />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={colorFor(entry.value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
