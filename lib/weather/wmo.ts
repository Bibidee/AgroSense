// WMO weather code → human label + visual kind.
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
