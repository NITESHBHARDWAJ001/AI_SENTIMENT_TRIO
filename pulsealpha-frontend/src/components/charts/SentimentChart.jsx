import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function SentimentChart({ data, showThresholds = false }) {
  return (
    <div className="h-72 min-h-[260px] w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%" minWidth={280}>
        <AreaChart data={data}>
          <CartesianGrid stroke="#263247" strokeDasharray="3 3" />
          <XAxis dataKey="date" stroke="#94A3B8" tickLine={false} axisLine={false} />
          <YAxis stroke="#94A3B8" tickLine={false} axisLine={false} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #263247" }} />
          {showThresholds ? <ReferenceLine y={0.2} stroke="#16A34A" strokeDasharray="5 5" /> : null}
          {showThresholds ? <ReferenceLine y={-0.2} stroke="#DC2626" strokeDasharray="5 5" /> : null}
          <Area type="monotone" dataKey="sentiment" stroke="#06B6D4" fill="#06B6D4" fillOpacity={0.2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
