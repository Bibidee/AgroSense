"use client";
import { useState, useTransition } from "react";
import { updateNotificationPrefs } from "@/server/actions/settings";

export function NotificationsForm({ prefs }: { prefs: any }) {
  const [state, setState] = useState({
    verdict_email: !!prefs.verdict_email,
    risk_email:    !!prefs.risk_email,
    weekly_digest: !!prefs.weekly_digest,
  });
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();

  function toggle(key: keyof typeof state) {
    setMsg(undefined);
    const next = { ...state, [key]: !state[key] };
    setState(next);
    start(async () => {
      const r = await updateNotificationPrefs(next);
      setMsg(r.ok ? "Saved" : (r.error || "Save failed"));
    });
  }
  const Row = ({ k, label, desc }: { k: keyof typeof state; label: string; desc: string }) => (
    <label className="flex items-start justify-between gap-3 py-2 cursor-pointer">
      <div>
        <div className="text-pearl text-sm">{label}</div>
        <div className="text-sage text-xs">{desc}</div>
      </div>
      <button type="button" onClick={() => toggle(k)} disabled={pending}
        className={`relative w-10 h-6 rounded-full transition ${state[k] ? "bg-biosignal" : "bg-white/10"}`}>
        <span className={`absolute top-0.5 ${state[k] ? "left-5" : "left-0.5"} w-5 h-5 rounded-full bg-pearl transition`} />
      </button>
    </label>
  );
  return (
    <div>
      <Row k="verdict_email" label="Verdict emails"  desc="Receive an email when a GenLayer verdict lands." />
      <Row k="risk_email"    label="Risk alerts"     desc="Storm Clay severity events on cases you own." />
      <Row k="weekly_digest" label="Weekly digest"   desc="Roll-up of new verdicts and contract activity." />
      {msg && <div className="text-xs text-sage mt-2">{msg}</div>}
    </div>
  );
}
