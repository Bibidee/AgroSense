"use server";
// Open-Meteo: https://open-meteo.com/  (no API key needed)
export async function fetchOpenMeteo(lat: number, lon: number) {
  if (Number.isNaN(lat) || Number.isNaN(lon)) {
    return { ok: false, error: "Farm coordinates missing." };
  }
  const url =
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
    `&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code` +
    `&current=weather_code,temperature_2m` +
    `&forecast_days=7&timezone=auto`;
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return { ok: false, error: `Open-Meteo HTTP ${r.status}` };
    const j: any = await r.json();
    const d = j.daily;
    if (!d?.time?.length) return { ok: false, error: "Open-Meteo returned no daily series." };

    const lines = d.time.map((day: string, i: number) => {
      const hi = d.temperature_2m_max[i]; const lo = d.temperature_2m_min[i];
      const mm = d.precipitation_sum[i];  const p  = d.precipitation_probability_max[i];
      return `${day}: ${lo}–${hi}°C · rain ${mm} mm · p ${p}%`;
    });
    const text =
      `7-day forecast (Open-Meteo, ${j.timezone ?? "local"}):\n` +
      lines.join("\n");
    return { ok: true, text, raw: j };
  } catch (e: any) {
    return { ok: false, error: e?.message ?? "Open-Meteo fetch failed" };
  }
}
