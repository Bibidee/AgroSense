import { supabaseServer } from "@/lib/supabase/server";
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
        { label: `Forecast`,
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
    { label: `Forecast`, val: "—", tone: "sensor" },
  ];
}
