import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useAuth } from "../../contexts/useAuth";

export function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    await signup(form);
    navigate("/app");
  };

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <h1 className="text-xl font-semibold">Create Account</h1>
      <Input placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
      <Button className="w-full" type="submit" disabled={submitting}>{submitting ? "Creating account..." : "Sign Up"}</Button>
      <p className="text-sm text-[#94A3B8]">
        Already have an account? <Link className="text-[#3B82F6]" to="/login">Login</Link>
      </p>
    </form>
  );
}
