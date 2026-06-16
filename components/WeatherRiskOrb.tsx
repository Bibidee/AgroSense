import { supabaseServer } from "@/lib/supabase/server";
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
      <div className="text-[10px] uppercase tracking-wider text-sage">Weather risk</div>
      <div className="flex flex-col items-center text-center gap-2 mt-3">
        <div className="relative h-20 w-20 rounded-full grid place-items-center shrink-0"
          style={{ background: `radial-gradient(circle at 30% 30%, ${ringColor}33, transparent 70%), conic-gradient(${ringColor}66, transparent 70%)` }}>
          <div className="absolute inset-2 rounded-full bg-obsidian border border-white/10 grid place-items-center">
            <WeatherGlyph kind={kind} size={56} />
          </div>
        </div>
        <div className="min-w-0 w-full">
          <div className="font-display text-pearl text-base leading-tight break-words">{label}</div>
          <div className="text-sage text-[11px] mt-1 capitalize">Risk: {level}</div>
          <div className="text-sage text-[10px]">Next 7-day forecast</div>
        </div>
      </div>
      <style>{`@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
