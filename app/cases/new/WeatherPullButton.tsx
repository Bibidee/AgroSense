"use client";
import { useState, useTransition } from "react";
import { fetchOpenMeteo } from "@/server/actions/weather";

// Auto-fills a textarea by name with Open-Meteo's 7-day summary for the
// currently selected farm. Reads coords from a hidden data attribute on the
// <option> elements so we don't need extra round-trips.
export function WeatherPullButton({ farms }: { farms: { id: string; latitude: number | null; longitude: number | null }[] }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();

  function onClick() {
    setMsg(undefined);
    const sel = document.querySelector<HTMLSelectElement>('select[name="farmId"]');
    const target = document.querySelector<HTMLTextAreaElement>('textarea[name="weatherContext"]');
    if (!sel || !target) { setMsg("Form not ready."); return; }
    const f = farms.find(x => x.id === sel.value);
    if (!f || f.latitude == null || f.longitude == null) {
      setMsg("Selected farm has no coordinates. Add lat/lon in /farms.");
      return;
    }
    start(async () => {
      const r = await fetchOpenMeteo(Number(f.latitude), Number(f.longitude));
      if (!r.ok) { setMsg(r.error || "Fetch failed"); return; }
      target.value = r.text!;
      setMsg("Live forecast filled in.");
    });
  }

  return (
    <div className="flex items-center gap-2">
      <button type="button" onClick={onClick} disabled={pending}
        className="btn-ghost text-xs disabled:opacity-60">
        {pending ? "Fetching…" : "Pull live weather"}
      </button>
      {msg && <span className="text-xs text-sage">{msg}</span>}
    </div>
  );
}
