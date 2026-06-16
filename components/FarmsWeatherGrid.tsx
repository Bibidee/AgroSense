import { supabaseServer } from "@/lib/supabase/server";
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
