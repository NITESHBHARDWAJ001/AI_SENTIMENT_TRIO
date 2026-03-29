import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export function OverlayChart({ data }) {
  return (
    <div className="h-72 min-h-[260px] w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%" minWidth={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="#263247" strokeDasharray="3 3" />
          <XAxis dataKey="date" stroke="#94A3B8" tickLine={false} axisLine={false} />
          <YAxis yAxisId="left" stroke="#94A3B8" tickLine={false} axisLine={false} />
          <YAxis yAxisId="right" orientation="right" stroke="#94A3B8" tickLine={false} axisLine={false} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #263247" }} />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="price" stroke="#3B82F6" strokeWidth={2} dot={false} />
          <Line yAxisId="right" type="monotone" dataKey="sentiment" stroke="#06B6D4" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
