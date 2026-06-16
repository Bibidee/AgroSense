import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        obsidian:   "#07110D",
        graphite:   "#101C17",
        ivory:      "#F4EFE4",
        pollen:     "#FFF9EC",
        // Signal palette
        biosignal:  "#39D98A",
        sensor:     "#00C2B8",
        yieldgold:  "#F2B84B",
        stormclay:  "#D65A46",
        consensus:  "#8B5CF6",
        // Text
        pearl:      "#F8F4EA",
        soil:       "#111A15",
        sage:       "#91A399",
        reed:       "#D9D2C3",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "ui-sans-serif", "system-ui"],
        body:    ["Inter", "ui-sans-serif", "system-ui"],
        mono:    ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: { xl: "14px", "2xl": "22px", "3xl": "28px" },
      boxShadow: {
        panel: "0 1px 0 rgba(199,214,199,0.06), 0 10px 40px -20px rgba(0,0,0,0.7)",
        glow:  "0 0 0 1px rgba(57,217,138,0.25), 0 0 32px -8px rgba(57,217,138,0.35)",
        violet:"0 0 0 1px rgba(139,92,246,0.35), 0 0 32px -8px rgba(139,92,246,0.45)",
      },
      backgroundImage: {
        "field-grid":
          "radial-gradient(circle at 20% 10%, rgba(57,217,138,0.05), transparent 40%), radial-gradient(circle at 80% 80%, rgba(0,194,184,0.04), transparent 40%), linear-gradient(180deg,#07110D 0%, #0a1612 100%)",
        "scanline":
          "repeating-linear-gradient(0deg, rgba(199,214,199,0.04) 0, rgba(199,214,199,0.04) 1px, transparent 1px, transparent 4px)",
      },
    },
  },
  plugins: [],
};
export default config;
