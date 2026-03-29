import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

export function ChartCard({ title, action, children, className = "" }) {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        {action}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
