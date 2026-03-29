import { useEffect, useState } from "react";
import { AlertCard } from "../../components/common/AlertCard";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { createAlert, deleteAlert, getAlerts } from "../../services/userService";

export function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [form, setForm] = useState({ ticker: "", message: "", trigger_value: "" });

  const load = async () => {
    const data = await getAlerts();
    setAlerts(data);
  };

  useEffect(() => {
    let mounted = true;
    getAlerts().then((data) => {
      if (mounted) {
        setAlerts(data);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  const onCreate = async (e) => {
    e.preventDefault();
    await createAlert({
      ticker: form.ticker,
      message: form.message,
      trigger_value: form.trigger_value ? Number(form.trigger_value) : null
    });
    setForm({ ticker: "", message: "", trigger_value: "" });
    await load();
  };

  const onDelete = async (id) => {
    await deleteAlert(id);
    await load();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Alerts</h1>
      <form onSubmit={onCreate} className="grid grid-cols-1 gap-3 rounded-2xl border border-[#263247] bg-[#172033] p-4 md:grid-cols-4">
        <Input placeholder="Ticker" value={form.ticker} onChange={(e) => setForm((p) => ({ ...p, ticker: e.target.value }))} />
        <Input placeholder="Alert message" value={form.message} onChange={(e) => setForm((p) => ({ ...p, message: e.target.value }))} />
        <Input type="number" step="0.01" placeholder="Trigger value (optional)" value={form.trigger_value} onChange={(e) => setForm((p) => ({ ...p, trigger_value: e.target.value }))} />
        <Button type="submit">Create Alert</Button>
      </form>

      <div className="space-y-3">
        {alerts.map((alert, idx) => (
          <div key={`${alert.ticker}-${idx}`} className="space-y-2">
            <AlertCard alert={alert} />
            <Button size="sm" variant="danger" onClick={() => onDelete(alert.id)}>Delete Alert</Button>
          </div>
        ))}
      </div>
    </div>
  );
}
