import { useEffect, useState } from "react";
import { useAuth } from "../../contexts/useAuth";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { getProfile, updateProfile } from "../../services/userService";

export function SettingsPage() {
  const { user, signout, setUserProfile } = useAuth();
  const [form, setForm] = useState({ name: "", email: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    getProfile()
      .then((profile) => {
        if (mounted) {
          setForm({
            name: profile?.name || user?.name || "",
            email: profile?.email || user?.email || ""
          });
        }
      })
      .catch(() => {
        if (mounted) {
          setForm({ name: user?.name || "", email: user?.email || "" });
        }
      });

    return () => {
      mounted = false;
    };
  }, [user]);

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    const result = await updateProfile(form);
    if (result?.user) {
      setUserProfile(result.user);
    }
    setSaving(false);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <form onSubmit={onSave} className="grid grid-cols-1 gap-3 rounded-2xl border border-[#263247] bg-[#172033] p-4 md:grid-cols-3">
        <Input placeholder="Your name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} />
        <Input type="email" placeholder="Your email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} />
        <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Update Profile"}</Button>
      </form>
      <div className="rounded-2xl border border-[#263247] bg-[#172033] p-4 text-sm">
        <p className="text-[#94A3B8]">Signed in as</p>
        <p className="font-semibold text-[#F9FAFB]">{user?.name || user?.email}</p>
      </div>
      <Button variant="danger" onClick={signout}>Logout</Button>
    </div>
  );
}
