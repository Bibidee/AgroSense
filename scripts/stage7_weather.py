"""
Stage 7 - live weather expansion + always-pulse dots + per-farm grid + animated orb.
Run:  python scripts/stage7_weather.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

# ---------- weather lookup helpers ----------
F["lib/weather/wmo.ts"] = r"""// WMO weather code → human label + visual kind.
// Open-Meteo returns daily `weathercode`. Source: https://open-meteo.com/en/docs
export type WeatherKind =
  | "clear" | "cloudy" | "fog" | "drizzle" | "rain" | "thunder" | "snow" | "showers";

export function wmoLabel(code: number | null | undefined): { label: string; kind: WeatherKind } {
  const c = Number(code);
  if (!Number.isFinite(c)) return { label: "Unknown", kind: "cloudy" };
  if (c === 0) return { label: "Clear sky", kind: "clear" };
  if (c <= 3) return { label: c === 1 ? "Mostly clear" : c === 2 ? "Partly cloudy" : "Overcast", kind: "cloudy" };
  if (c === 45 || c === 48) return { label: "Fog", kind: "fog" };
  if (c >= 51 && c <= 57) return { label: "Drizzle", kind: "drizzle" };
  if (c >= 61 && c <= 67) return { label: "Rain", kind: "rain" };
  if (c >= 71 && c <= 77) return { label: "Snow", kind: "snow" };
  if (c >= 80 && c <= 82) return { label: "Showers", kind: "showers" };
  if (c >= 95) return { label: "Thunderstorm", kind: "thunder" };
  return { label: "Mixed", kind: "cloudy" };
}

export function riskFromCode(code: number | null | undefined): "low" | "moderate" | "high" {
  const c = Number(code);
  if (!Number.isFinite(c)) return "moderate";
  if (c >= 95) return "high";
  if (c >= 80) return "high";
  if (c >= 61) return "moderate";
  if (c >= 45) return "moderate";
  if (c >= 51) return "moderate";
  return "low";
}
"""

# ---------- Animated weather glyph ----------
F["components/WeatherGlyph.tsx"] = r"""import type { WeatherKind } from "@/lib/weather/wmo";

// Inline animated SVG per WMO category. No client JS needed.
export function WeatherGlyph({ kind, size = 80 }: { kind: WeatherKind; size?: number }) {
  const s = size;
  if (kind === "clear") {
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        <defs>
          <radialGradient id="sun" cx="50%" cy="50%" r="50%">
            <stop offset="0%"  stopColor="#FFE39A" />
            <stop offset="60%" stopColor="#F2B84B" />
            <stop offset="100%" stopColor="#D6911E" />
          </radialGradient>
        </defs>
        <g style={{ transformOrigin: "50px 50px", animation: "spin 14s linear infinite" }}>
          {[0,30,60,90,120,150,180,210,240,270,300,330].map(a => (
            <rect key={a} x="49" y="6" width="2" height="14" fill="#F2B84B" opacity="0.85"
              transform={`rotate(${a} 50 50)`} />
          ))}
        </g>
        <circle cx="50" cy="50" r="22" fill="url(#sun)" />
        <circle cx="50" cy="50" r="22" fill="none" stroke="#F2B84B" strokeOpacity="0.4">
          <animate attributeName="r" values="22;26;22" dur="2.2s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.4;0;0.4" dur="2.2s" repeatCount="indefinite" />
        </circle>
      </svg>
    );
  }
  if (kind === "cloudy") {
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        <g fill="#9aa9a0" opacity="0.85">
          <ellipse cx="40" cy="58" rx="22" ry="14">
            <animate attributeName="cx" values="40;46;40" dur="6s" repeatCount="indefinite" />
          </ellipse>
          <ellipse cx="62" cy="52" rx="20" ry="12" fill="#c4d0c8">
            <animate attributeName="cx" values="62;56;62" dur="7s" repeatCount="indefinite" />
          </ellipse>
        </g>
      </svg>
    );
  }
  if (kind === "fog") {
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        {[34,46,58,70].map((y, i) => (
          <rect key={y} x="10" y={y} width="80" height="4" rx="2" fill="#c8d4cc" opacity="0.55">
            <animate attributeName="x" values={`-10;10;-10`} dur={`${5 + i}s`} repeatCount="indefinite" />
          </rect>
        ))}
      </svg>
    );
  }
  if (kind === "drizzle" || kind === "rain" || kind === "showers") {
    const heavy = kind !== "drizzle";
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        <ellipse cx="50" cy="38" rx="28" ry="14" fill="#9aa9a0" />
        <ellipse cx="62" cy="32" rx="18" ry="10" fill="#c4d0c8" />
        {[28,42,56,70].map((x, i) => (
          <line key={x} x1={x} y1="56" x2={x - 4} y2={heavy ? 84 : 76}
            stroke={kind === "showers" ? "#00C2B8" : "#39D98A"} strokeWidth={heavy ? 2 : 1.5} strokeLinecap="round" opacity="0.85">
            <animate attributeName="y1" values="56;88;56" dur={`${0.9 + i * 0.15}s`} repeatCount="indefinite" />
            <animate attributeName="y2" values={`${heavy ? 84 : 76};110;${heavy ? 84 : 76}`} dur={`${0.9 + i * 0.15}s`} repeatCount="indefinite" />
          </line>
        ))}
      </svg>
    );
  }
  if (kind === "thunder") {
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        <ellipse cx="50" cy="36" rx="30" ry="15" fill="#5e6a63" />
        <ellipse cx="64" cy="30" rx="18" ry="10" fill="#7e8a82" />
        <polygon points="48,52 56,52 50,68 60,68 44,90 48,72 40,72" fill="#F2B84B">
          <animate attributeName="opacity" values="0.4;1;0.4" dur="0.8s" repeatCount="indefinite" />
        </polygon>
      </svg>
    );
  }
  if (kind === "snow") {
    return (
      <svg viewBox="0 0 100 100" width={s} height={s} aria-hidden>
        <ellipse cx="50" cy="36" rx="28" ry="14" fill="#c4d0c8" />
        {[30,46,62,78].map((x, i) => (
          <text key={x} x={x} y="78" fontSize="10" fill="#F8F4EA" opacity="0.9">
            ❄
            <animate attributeName="y" values="56;90;56" dur={`${1.6 + i * 0.2}s`} repeatCount="indefinite" />
          </text>
        ))}
      </svg>
    );
  }
  return null;
}
"""

# ---------- WeatherRiskOrb: animated, real conditions ----------
F["components/WeatherRiskOrb.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { fetchOpenMeteo } from "@/server/actions/weather";
import { WeatherGlyph } from "./WeatherGlyph";
import { wmoLabel, riskFromCode } from "@/lib/weather/wmo";

export async function WeatherRiskOrb() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farm } = me.user
    ? await sb.from("farms").select("latitude,longitude,name")
        .eq("user_id", me.user.id)
        .not("latitude", "is", null).not("longitude", "is", null)
        .order("created_at", { ascending: true }).limit(1).maybeSingle()
    : { data: null };

  let label = "Add coordinates";
  let kind: any = "cloudy";
  let level: "low"|"moderate"|"high" = "moderate";
  let farmName = "—";

  if (farm?.latitude != null && farm?.longitude != null) {
    farmName = (farm.name as string) || farmName;
    const r: any = await fetchOpenMeteo(Number(farm.latitude), Number(farm.longitude));
    const code = r.ok ? (r.raw?.daily?.weathercode?.[0]
                        ?? r.raw?.current?.weathercode
                        ?? r.raw?.daily?.weather_code?.[0]) : null;
    const meta = wmoLabel(code);
    label = meta.label; kind = meta.kind;
    level = riskFromCode(code);
  }

  const ringColor = level === "high" ? "#D65A46" : level === "moderate" ? "#F2B84B" : "#39D98A";
  return (
    <div className="panel p-5 lift relative overflow-hidden">
      <div className="text-[10px] uppercase tracking-wider text-sage flex items-center justify-between">
        <span>Weather risk</span>
        <span className="font-mono text-[10px] text-sage truncate ml-2">{farmName}</span>
      </div>
      <div className="flex items-center gap-4 mt-3">
        <div className="relative h-24 w-24 rounded-full grid place-items-center shrink-0"
          style={{ background: `radial-gradient(circle at 30% 30%, ${ringColor}33, transparent 70%), conic-gradient(${ringColor}66, transparent 70%)` }}>
          <div className="absolute inset-2 rounded-full bg-obsidian border border-white/10 grid place-items-center">
            <WeatherGlyph kind={kind} size={64} />
          </div>
        </div>
        <div className="min-w-0">
          <div className="font-display text-pearl text-lg leading-tight">{label}</div>
          <div className="text-sage text-xs mt-1 capitalize">Risk: {level}</div>
          <div className="text-sage text-[10px] mt-1">Next 7-day forecast</div>
        </div>
      </div>
      <style>{`@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
"""

# ---------- Per-farm weather grid ----------
F["components/FarmsWeatherGrid.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { fetchOpenMeteo } from "@/server/actions/weather";
import { WeatherGlyph } from "./WeatherGlyph";
import { wmoLabel, riskFromCode } from "@/lib/weather/wmo";

export async function FarmsWeatherGrid() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return null;
  const { data: farms } = await sb.from("farms")
    .select("id,name,country,region,latitude,longitude")
    .eq("user_id", me.user.id)
    .not("latitude", "is", null).not("longitude", "is", null)
    .order("created_at", { ascending: false });

  if (!farms?.length) {
    return (
      <div className="panel p-5 text-sage text-sm">
        Add at least one farm with coordinates to see per-farm forecasts.
      </div>
    );
  }

  const rows = await Promise.all(farms.map(async f => {
    const r: any = await fetchOpenMeteo(Number(f.latitude), Number(f.longitude));
    const d = r.ok ? r.raw?.daily : null;
    const code = d?.weathercode?.[0] ?? d?.weather_code?.[0] ?? null;
    const meta = wmoLabel(code);
    const tHi = d?.temperature_2m_max?.[0] ?? null;
    const tLo = d?.temperature_2m_min?.[0] ?? null;
    const rainP = d?.precipitation_probability_max?.[0] ?? null;
    const rainMM = d?.precipitation_sum?.[0] ?? null;
    return { farm: f, ok: r.ok, kind: meta.kind, label: meta.label, level: riskFromCode(code), tHi, tLo, rainP, rainMM };
  }));

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Per-farm live weather</div>
        <span className="badge badge-sensor"><i className="dot dot-sensor pulse"></i>Open-Meteo</span>
      </div>
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {rows.map(({ farm, ok, kind, label, level, tHi, tLo, rainP, rainMM }) => {
          const ringColor = level === "high" ? "#D65A46" : level === "moderate" ? "#F2B84B" : "#39D98A";
          const tone = level === "high" ? "risk" : level === "moderate" ? "gold" : "bio";
          return (
            <div key={farm.id} className="rounded-xl border border-white/5 bg-obsidian/40 p-4 flex gap-3">
              <div className="relative h-16 w-16 shrink-0 rounded-full grid place-items-center"
                style={{ background: `radial-gradient(circle at 30% 30%, ${ringColor}33, transparent 70%), conic-gradient(${ringColor}66, transparent 70%)` }}>
                <div className="absolute inset-1.5 rounded-full bg-obsidian border border-white/10 grid place-items-center">
                  <WeatherGlyph kind={kind} size={44} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display text-pearl truncate">{farm.name}</div>
                <div className="text-[10px] text-sage truncate">{farm.region ? `${farm.region}, ` : ""}{farm.country}</div>
                <div className="text-pearl text-sm mt-1 flex items-center gap-2">
                  <i className={`dot dot-${tone} pulse`}></i>{ok ? label : "Unavailable"}
                </div>
                {ok && (
                  <div className="text-[11px] text-sage mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                    {tLo != null && tHi != null && <span>{Math.round(tLo)}–{Math.round(tHi)}°C</span>}
                    {rainP != null && <span>rain {rainP}%</span>}
                    {rainMM != null && <span>{rainMM} mm</span>}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
"""

# ---------- SignalStrip: always-pulse dots ----------
F["components/SignalStrip.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { fetchOpenMeteo } from "@/server/actions/weather";

type Tone = "bio" | "sensor" | "gold" | "risk" | "violet";
interface Cell { label: string; val: string; tone: Tone }

function rainfallTone(p: number | null): Tone {
  if (p == null) return "sensor";
  if (p >= 70) return "risk";
  if (p >= 40) return "gold";
  return "bio";
}
function tempTone(t: number | null): Tone {
  if (t == null) return "sensor";
  if (t >= 33 || t <= 10) return "risk";
  if (t >= 30) return "gold";
  return "bio";
}

export async function SignalStrip() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farm } = me.user
    ? await sb.from("farms").select("latitude,longitude,name")
        .eq("user_id", me.user.id)
        .not("latitude", "is", null).not("longitude", "is", null)
        .order("created_at", { ascending: true }).limit(1).maybeSingle()
    : { data: null };

  let cells: Cell[];
  let live = false;
  let farmTag = "Add farm coords";

  if (farm?.latitude != null && farm?.longitude != null) {
    farmTag = (farm.name as string) || farmTag;
    const r: any = await fetchOpenMeteo(Number(farm.latitude), Number(farm.longitude));
    if (r.ok && r.raw?.daily) {
      live = true;
      const d = r.raw.daily;
      const rainP  = d.precipitation_probability_max?.[0] ?? null;
      const rainMM = d.precipitation_sum?.[0] ?? null;
      const tHi    = d.temperature_2m_max?.[0] ?? null;
      const tLo    = d.temperature_2m_min?.[0] ?? null;
      cells = [
        { label: "Rainfall",      val: rainP != null ? `${rainP}%` : "—",                                tone: rainfallTone(rainP) },
        { label: "Temperature",   val: tHi != null ? `${Math.round(tHi)}°C` : "—",                       tone: tempTone(tHi) },
        { label: "Soil moisture", val: rainMM != null && rainMM > 6 ? "Saturated" : rainMM != null && rainMM > 1 ? "Moderate" : "Dry",
          tone: rainMM != null && rainMM > 6 ? "risk" : rainMM != null && rainMM > 1 ? "bio" : "gold" },
        { label: "Market signal", val: "Positive",                                                       tone: "gold"   },
        { label: "Pest risk",     val: tHi != null && tHi >= 30 && rainMM != null && rainMM > 3 ? "Elevated" : "Low",
          tone: tHi != null && tHi >= 30 && rainMM != null && rainMM > 3 ? "risk" : "bio" },
        { label: `Forecast · ${farmTag.slice(0, 14)}`,
          val: tLo != null && tHi != null ? `${Math.round(tLo)}–${Math.round(tHi)}°C` : "—",             tone: "sensor" },
      ];
    } else {
      cells = fallback(farmTag);
    }
  } else {
    cells = fallback(farmTag);
  }

  return (
    <div className="panel p-1 grid grid-cols-2 md:grid-cols-6 gap-1 overflow-hidden">
      {cells.map((c, i) => (
        <div key={i} className="px-4 py-3 rounded-xl bg-obsidian/40 border border-white/5">
          <div className="text-[10px] uppercase tracking-wider text-sage flex items-center justify-between gap-2">
            <span className="truncate">{c.label}</span>
            {live && i === 0 && <span className="badge badge-sensor !py-0 !px-1.5 !text-[9px]">LIVE</span>}
          </div>
          <div className="font-display text-pearl mt-1 flex items-center gap-2">
            <i className={`dot dot-${c.tone} pulse`}></i>
            {c.val}
          </div>
        </div>
      ))}
    </div>
  );
}

function fallback(farmTag: string): Cell[] {
  return [
    { label: "Rainfall",      val: "—",        tone: "sensor" },
    { label: "Temperature",   val: "—",        tone: "gold"   },
    { label: "Soil moisture", val: "Moderate", tone: "bio"    },
    { label: "Market signal", val: "Positive", tone: "gold"   },
    { label: "Pest risk",     val: "Low",      tone: "bio"    },
    { label: `Forecast · ${farmTag.slice(0, 14)}`, val: "—",   tone: "sensor" },
  ];
}
"""

# ---------- Dashboard wiring: drop FarmsWeatherGrid in ----------
F["app/dashboard/page.tsx"] = r"""import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { WeatherRiskOrb } from "@/components/WeatherRiskOrb";
import { SignalStrip } from "@/components/SignalStrip";
import { EvidenceStrengthMeter } from "@/components/EvidenceStrengthMeter";
import { CropWindowTimeline } from "@/components/CropWindowTimeline";
import { ContractActivityStream } from "@/components/ContractActivityStream";
import { FarmsWeatherGrid } from "@/components/FarmsWeatherGrid";
import { LiveBadge } from "@/components/Badges";

export default async function DashboardPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const userId = me.user!.id;

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,crop_type,status,created_at,decision_type").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(8);
  const { data: latest } = await sb.from("genlayer_verdicts")
    .select("*").eq("user_id", userId).order("created_at", { ascending: false }).limit(1).maybeSingle();
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("action,status,transaction_hash,created_at").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(5);

  return (
    <AppShell section="Mission control" subtitle="Live agricultural decision OS">
      <div className="space-y-6">
        <SignalStrip />

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-7">
            <VerdictCapsule v={latest} status={latest ? "consensus_reached" : "not_submitted"} />
          </div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-2"><WeatherRiskOrb /></div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-3">
            <GenLayerConsensusPanel v={latest} status={latest ? "consensus_reached" : "not_submitted"} />
          </div>
        </div>

        <FarmsWeatherGrid />

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8">
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between px-5 pt-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-sage">Active case matrix</div>
                  <div className="font-display text-pearl text-lg">Recent advisories</div>
                </div>
                <div className="flex items-center gap-2">
                  <Link href="/cases" className="btn-ghost text-sm">All cases</Link>
                  <Link href="/cases/new" className="btn-primary text-sm">+ New case</Link>
                </div>
              </div>
              <table className="os mt-3">
                <thead><tr><th>Crop</th><th>Decision</th><th>Status</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {(cases ?? []).length === 0 && (
                    <tr><td colSpan={5} className="text-center text-sage py-10">No cases yet. Open a new advisory to engage GenLayer validators.</td></tr>
                  )}
                  {(cases ?? []).map(c => (
                    <tr key={c.id}>
                      <td className="font-display text-pearl">{c.crop_type}</td>
                      <td className="text-pearl/80">{c.decision_type}</td>
                      <td><span className="badge badge-sensor">{c.status}</span></td>
                      <td className="text-sage">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td><Link href={`/cases/${c.id}`} className="text-biosignal">Open →</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4"><EvidenceStrengthMeter score={latest ? 78 : 35} /></div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><CropWindowTimeline /></div>
          <div className="col-span-12 lg:col-span-4"><ContractActivityStream items={activity ?? []} /></div>
        </div>
      </div>
    </AppShell>
  );
}
"""

def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage7] wrote {n} files")

if __name__ == "__main__":
    main()
