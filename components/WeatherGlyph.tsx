import type { WeatherKind } from "@/lib/weather/wmo";

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
