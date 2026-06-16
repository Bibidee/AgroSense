"use client";
import { useEffect, useState } from "react";
import { fetchOpenMeteo } from "@/server/actions/weather";
import { wmoLabel, riskFromCode } from "@/lib/weather/wmo";
import { WeatherGlyph } from "./WeatherGlyph";

// Browser-geolocation weather. Shows "your current location", not the farm.
// Useful to decide whether you can drive out today.
export function OperatorWeather() {
  const [state, setState] = useState<
    | { phase: "idle" }
    | { phase: "asking" }
    | { phase: "loading" }
    | { phase: "denied"; msg: string }
    | { phase: "ready"; kind: any; label: string; level: "low" | "moderate" | "high"; tHi: number | null; tLo: number | null; rainP: number | null; place: string }
  >({ phase: "idle" });

  async function start() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setState({ phase: "denied", msg: "Geolocation not supported." });
      return;
    }
    setState({ phase: "asking" });
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        setState({ phase: "loading" });
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const r: any = await fetchOpenMeteo(lat, lon);
        if (!r.ok || !r.raw?.daily) {
          setState({ phase: "denied", msg: r.error || "Forecast unavailable." });
          return;
        }
        const d = r.raw.daily;
        const code = d.weather_code?.[0] ?? d.weathercode?.[0] ?? r.raw?.current?.weather_code ?? null;
        const meta = wmoLabel(code);
        setState({
          phase: "ready",
          kind: meta.kind,
          label: meta.label,
          level: riskFromCode(code),
          tHi: d.temperature_2m_max?.[0] ?? null,
          tLo: d.temperature_2m_min?.[0] ?? null,
          rainP: d.precipitation_probability_max?.[0] ?? null,
          place: `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`,
        });
      },
      (err) => setState({ phase: "denied", msg: err.message || "Location denied." }),
      { enableHighAccuracy: false, maximumAge: 10 * 60 * 1000, timeout: 8000 }
    );
  }

  // Don't prompt automatically — wait for explicit click.
  useEffect(() => {}, []);

  if (state.phase === "ready") {
    const ringColor = state.level === "high" ? "#D65A46" : state.level === "moderate" ? "#F2B84B" : "#39D98A";
    return (
      <div className="panel p-5 lift">
        <div className="flex items-center justify-between">
          <div className="text-[10px] uppercase tracking-wider text-sage">You are here</div>
          <span className="badge badge-sensor"><i className="dot dot-sensor pulse"></i>Live</span>
        </div>
        <div className="flex items-center gap-3 mt-3">
          <div className="relative h-16 w-16 rounded-full grid place-items-center shrink-0"
            style={{ background: `radial-gradient(circle at 30% 30%, ${ringColor}33, transparent 70%), conic-gradient(${ringColor}66, transparent 70%)` }}>
            <div className="absolute inset-1.5 rounded-full bg-obsidian border border-white/10 grid place-items-center">
              <WeatherGlyph kind={state.kind} size={44} />
            </div>
          </div>
          <div className="min-w-0">
            <div className="font-display text-pearl text-base leading-tight break-words">{state.label}</div>
            <div className="text-[11px] text-sage mt-0.5">
              {state.tLo != null && state.tHi != null && <span>{Math.round(state.tLo)}–{Math.round(state.tHi)}°C</span>}
              {state.rainP != null && <span> · rain {state.rainP}%</span>}
            </div>
            <div className="font-mono text-[10px] text-sage mt-0.5">{state.place}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel p-5">
      <div className="text-[10px] uppercase tracking-wider text-sage">You are here</div>
      <div className="font-display text-pearl text-base mt-2">Operator location weather</div>
      <p className="text-sage text-xs mt-1">Quick check whether <em>you</em> can travel today. Browser geolocation only — never stored.</p>
      <button onClick={start} disabled={state.phase === "asking" || state.phase === "loading"}
        className="btn-ghost text-sm mt-3 disabled:opacity-60">
        {state.phase === "asking" ? "Asking browser…"
          : state.phase === "loading" ? "Fetching forecast…"
          : "Use my location"}
      </button>
      {state.phase === "denied" && (
        <div className="text-stormclay text-xs mt-2">{state.msg}</div>
      )}
    </div>
  );
}
