import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useAuth } from "../../contexts/useAuth";

export function LoginPage() {
  const navigate = useNavigate();
  const { signin } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    await signin(form);
    navigate("/app");
  };

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <h1 className="text-xl font-semibold">Login</h1>
      <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
      <Button className="w-full" type="submit" disabled={submitting}>{submitting ? "Signing in..." : "Sign In"}</Button>
      <p className="text-sm text-[#94A3B8]">
        No account? <Link className="text-[#3B82F6]" to="/signup">Create one</Link>
      </p>
    </form>
  );
}
