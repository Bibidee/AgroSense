"""
Stage 4 - Field Intelligence OS UI transformation.
- New color tokens, fonts, globals.
- New AppShell + command rail + intelligence rail components.
- All pages rewritten visually; server actions/form fields unchanged.
Run:  python scripts/stage4_ui.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

# =========================================================================
#                            DESIGN SYSTEM
# =========================================================================

F["tailwind.config.ts"] = r"""import type { Config } from "tailwindcss";
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
"""

F["app/globals.css"] = r"""@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root { color-scheme: dark; }
html, body {
  background: #07110D;
  color: #F8F4EA;
  font-family: Inter, ui-sans-serif, system-ui;
  -webkit-font-smoothing: antialiased;
}
.font-display { font-family: 'Space Grotesk', ui-sans-serif, system-ui; letter-spacing: -0.01em; }
.font-mono    { font-family: 'JetBrains Mono', ui-monospace, monospace; }

/* ----- Panels ----- */
.panel {
  background: linear-gradient(180deg, rgba(16,28,23,0.85), rgba(16,28,23,0.65));
  border: 1px solid rgba(199,214,199,0.10);
  border-radius: 22px;
  box-shadow: 0 1px 0 rgba(199,214,199,0.04), 0 30px 60px -30px rgba(0,0,0,0.8);
  backdrop-filter: blur(8px);
}
.panel-ivory {
  background: #F4EFE4;
  color: #111A15;
  border: 1px solid #D9D2C3;
  border-radius: 22px;
}
.panel-pollen {
  background: #FFF9EC;
  color: #111A15;
  border: 1px solid #D9D2C3;
  border-radius: 22px;
}
.panel-violet {
  background: linear-gradient(180deg, rgba(139,92,246,0.12), rgba(16,28,23,0.6));
  border: 1px solid rgba(139,92,246,0.35);
  border-radius: 22px;
}

/* ----- Buttons ----- */
.btn-primary {
  background: linear-gradient(180deg, #39D98A, #2BB874);
  color: #07110D; font-weight: 600;
  padding: 10px 18px; border-radius: 12px;
  box-shadow: 0 8px 24px -8px rgba(57,217,138,0.45);
  transition: transform .15s ease;
}
.btn-primary:hover { transform: translateY(-1px); }
.btn-ghost {
  background: rgba(199,214,199,0.06);
  color: #F8F4EA;
  border: 1px solid rgba(199,214,199,0.16);
  padding: 10px 18px; border-radius: 12px;
}
.btn-ghost:hover { background: rgba(199,214,199,0.12); }
.btn-violet {
  background: linear-gradient(180deg, #8B5CF6, #6D45E6);
  color: #fff; font-weight: 600;
  padding: 10px 18px; border-radius: 12px;
  box-shadow: 0 8px 24px -8px rgba(139,92,246,0.6);
}

/* ----- Form inputs ----- */
.input {
  width: 100%;
  background: rgba(7,17,13,0.6);
  border: 1px solid rgba(199,214,199,0.14);
  border-radius: 12px;
  padding: 11px 14px;
  color: #F8F4EA;
  font-size: 14px;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.input:focus { outline: none; border-color: #39D98A; box-shadow: 0 0 0 3px rgba(57,217,138,0.18); }
.input-light {
  width: 100%; background: #FFF9EC; color: #111A15;
  border: 1px solid #D9D2C3; border-radius: 12px;
  padding: 11px 14px; font-size: 14px;
}

/* ----- Badges ----- */
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
.badge-consensus { background: rgba(139,92,246,0.14); color: #c4b1ff; border: 1px solid rgba(139,92,246,0.4); }
.badge-bio       { background: rgba(57,217,138,0.12); color: #8df0bb; border: 1px solid rgba(57,217,138,0.35); }
.badge-sensor    { background: rgba(0,194,184,0.12); color: #66e6df; border: 1px solid rgba(0,194,184,0.35); }
.badge-gold      { background: rgba(242,184,75,0.14); color: #ffd58a; border: 1px solid rgba(242,184,75,0.35); }
.badge-risk      { background: rgba(214,90,70,0.14); color: #ff9d8a; border: 1px solid rgba(214,90,70,0.4); }
.badge-muted     { background: rgba(145,163,153,0.12); color: #c2cfc8; border: 1px solid rgba(145,163,153,0.25); }

/* ----- Dots ----- */
.dot { width: 8px; height: 8px; border-radius: 999px; box-shadow: 0 0 12px currentColor; }
.dot-bio    { color: #39D98A; background: #39D98A; }
.dot-sensor { color: #00C2B8; background: #00C2B8; }
.dot-violet { color: #8B5CF6; background: #8B5CF6; }
.dot-gold   { color: #F2B84B; background: #F2B84B; }
.dot-risk   { color: #D65A46; background: #D65A46; }

/* ----- Pulse ----- */
@keyframes consensus-pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(139,92,246,0.35); }
  50%     { box-shadow: 0 0 0 8px rgba(139,92,246,0); }
}
.pulse-consensus { animation: consensus-pulse 2.4s ease-in-out infinite; }

/* ----- Scanline overlay ----- */
.scanline::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(199,214,199,0.025) 0, rgba(199,214,199,0.025) 1px, transparent 1px, transparent 4px);
  border-radius: inherit;
}

/* ----- Hover lift ----- */
.lift { transition: transform .18s ease, box-shadow .18s ease; }
.lift:hover { transform: translateY(-2px); box-shadow: 0 24px 48px -28px rgba(0,0,0,0.8); }

/* ----- Divider ----- */
.hr { height: 1px; background: linear-gradient(90deg, transparent, rgba(199,214,199,0.18), transparent); border: 0; }

/* ----- Tables ----- */
table.os { width: 100%; border-collapse: separate; border-spacing: 0; }
table.os th { text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #91A399; padding: 12px 16px; background: rgba(7,17,13,0.5); border-bottom: 1px solid rgba(199,214,199,0.08); }
table.os td { padding: 14px 16px; border-bottom: 1px solid rgba(199,214,199,0.06); font-size: 14px; }
table.os tr:hover td { background: rgba(57,217,138,0.03); }

/* Light variant */
.light-surface table.os th { background: rgba(217,210,195,0.5); color: #5b6c64; border-bottom: 1px solid #D9D2C3; }
.light-surface table.os td { border-bottom: 1px solid #e6e0d1; color: #111A15; }
"""

# =========================================================================
#                              COMPONENTS
# =========================================================================

F["components/Brand.tsx"] = r"""export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "h-10 w-10" : size === "sm" ? "h-7 w-7" : "h-9 w-9";
  const font = size === "lg" ? "text-2xl" : size === "sm" ? "text-base" : "text-lg";
  return (
    <div className="flex items-center gap-2.5">
      <div className={`${dim} rounded-xl relative overflow-hidden`}
        style={{ background: "linear-gradient(135deg,#39D98A,#00C2B8 60%,#8B5CF6)" }}>
        <div className="absolute inset-[3px] rounded-[10px] bg-obsidian grid place-items-center text-biosignal font-display font-bold">A</div>
      </div>
      <div className="leading-none">
        <div className={`font-display font-bold text-pearl ${font}`}>AgroSense</div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-sage mt-1">Field Intelligence OS</div>
      </div>
    </div>
  );
}
"""

F["components/Badges.tsx"] = r"""export const ConsensusBadge = ({ label = "Consensus reached" }: { label?: string }) =>
  <span className="badge badge-consensus"><i className="dot dot-violet"></i>{label}</span>;

export const SourceOfTruthBadge = () =>
  <span className="badge badge-consensus">Source of truth · GenLayer</span>;

export const RiskBadge = ({ level }: { level: string }) =>
  <span className="badge badge-risk"><i className="dot dot-risk"></i>{level}</span>;

export const ActionWindowBadge = ({ window: w }: { window: string }) =>
  <span className="badge badge-gold"><i className="dot dot-gold"></i>{w}</span>;

export const LiveBadge = ({ label = "Live" }: { label?: string }) =>
  <span className="badge badge-sensor"><i className="dot dot-sensor pulse-consensus"></i>{label}</span>;

export const HealthBadge = ({ label = "Healthy" }: { label?: string }) =>
  <span className="badge badge-bio"><i className="dot dot-bio"></i>{label}</span>;
"""

F["components/HashText.tsx"] = r"""export function HashText({ value, label }: { value?: string | null; label?: string }) {
  if (!value) return <span className="font-mono text-xs text-sage">—</span>;
  const short = value.length > 18 ? `${value.slice(0,8)}…${value.slice(-6)}` : value;
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs">
      {label && <span className="text-sage uppercase tracking-wider text-[10px]">{label}</span>}
      <span className="text-pearl/90">{short}</span>
    </span>
  );
}
"""

F["components/CommandRail.tsx"] = r""""use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./Brand";
import { ConsensusBadge } from "./Badges";

const NAV = [
  { href: "/dashboard", label: "Dashboard", glyph: "◎" },
  { href: "/farms",     label: "Farms",     glyph: "▦" },
  { href: "/cases/new", label: "New case",  glyph: "+" },
  { href: "/evidence",  label: "Evidence",  glyph: "▣" },
  { href: "/profile",   label: "Profile",   glyph: "◐" },
  { href: "/settings",  label: "Settings",  glyph: "⚙" },
];

export function CommandRail({ admin, email, wallet }: { admin?: boolean; email?: string | null; wallet?: string | null }) {
  const path = usePathname();
  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-white/5 bg-graphite/60 backdrop-blur-md">
      <div className="px-5 pt-5 pb-4"><Brand /></div>
      <div className="px-3 pt-2 pb-3"><div className="hr" /></div>
      <nav className="flex-1 px-3 space-y-1">
        {NAV.map(n => {
          const active = path === n.href || (n.href !== "/dashboard" && path?.startsWith(n.href));
          return (
            <Link key={n.href} href={n.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition
                ${active
                  ? "bg-biosignal/10 text-biosignal border border-biosignal/30 shadow-glow"
                  : "text-pearl/80 hover:text-pearl hover:bg-white/5 border border-transparent"}`}>
              <span className={`w-6 h-6 grid place-items-center rounded-md text-xs ${active ? "bg-biosignal/20" : "bg-white/5"}`}>{n.glyph}</span>
              <span>{n.label}</span>
              {active && <span className="ml-auto dot dot-bio"></span>}
            </Link>
          );
        })}
        {admin && (
          <Link href="/admin"
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm mt-3
              ${path?.startsWith("/admin") ? "bg-consensus/15 text-pearl border border-consensus/40 shadow-violet" : "text-pearl/80 hover:bg-white/5 border border-transparent"}`}>
            <span className="w-6 h-6 grid place-items-center rounded-md text-xs bg-consensus/20">◈</span>
            <span>Admin console</span>
          </Link>
        )}
      </nav>
      <div className="px-4 pb-3">
        <div className="panel-violet p-3 text-xs">
          <ConsensusBadge label="GenLayer StudioNet" />
          <div className="font-mono text-[10px] text-sage mt-2 break-all">0x0eb53e72…E017f1</div>
        </div>
      </div>
      <div className="px-3 pb-4">
        <div className="rounded-xl border border-white/10 bg-obsidian/70 p-3">
          <div className="text-[10px] uppercase tracking-wider text-sage">Operator</div>
          <div className="text-sm text-pearl truncate">{email ?? "—"}</div>
          {wallet && <div className="font-mono text-[10px] text-sage mt-1 break-all">{wallet.slice(0,10)}…{wallet.slice(-6)}</div>}
        </div>
      </div>
    </aside>
  );
}
"""

F["components/TopContextBar.tsx"] = r"""import Link from "next/link";
import { LiveBadge } from "./Badges";
import { logOut } from "@/server/actions/auth";

export function TopContextBar({ section, subtitle }: { section: string; subtitle?: string }) {
  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-obsidian/80 backdrop-blur-md">
      <div className="flex items-center justify-between px-6 py-3">
        <div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-sage">Field Intelligence OS</div>
          <div className="font-display text-lg text-pearl">{section}</div>
          {subtitle && <div className="text-xs text-sage">{subtitle}</div>}
        </div>
        <div className="flex items-center gap-3">
          <LiveBadge label="Network live" />
          <Link href="/cases/new" className="btn-primary text-sm">+ Create advisory case</Link>
          <form action={logOut}><button className="btn-ghost text-sm">Sign out</button></form>
        </div>
      </div>
    </header>
  );
}
"""

F["components/AppShell.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { CommandRail } from "./CommandRail";
import { TopContextBar } from "./TopContextBar";

export async function AppShell({
  section, subtitle, children,
}: { section: string; subtitle?: string; children: React.ReactNode }) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: profile } = await sb.from("profiles").select("role,email").eq("user_id", me.user.id).maybeSingle();
  const { data: wallet } = await sb.from("wallets").select("address").eq("user_id", me.user.id).maybeSingle();

  return (
    <div className="min-h-screen bg-field-grid">
      <div className="flex">
        <CommandRail admin={profile?.role === "admin"} email={profile?.email ?? me.user.email} wallet={wallet?.address} />
        <div className="flex-1 min-w-0">
          <TopContextBar section={section} subtitle={subtitle} />
          <main className="px-6 py-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
"""

F["components/SignalStrip.tsx"] = r"""export function SignalStrip() {
  const cells = [
    { label: "Rainfall",      val: "62%", tone: "sensor" },
    { label: "Temperature",   val: "30°C", tone: "gold"  },
    { label: "Soil moisture", val: "Moderate", tone: "bio" },
    { label: "Market signal", val: "Positive", tone: "gold" },
    { label: "Pest risk",     val: "Low",      tone: "bio" },
    { label: "Window",        val: "7–14 d",   tone: "sensor" },
  ];
  return (
    <div className="panel p-1 grid grid-cols-2 md:grid-cols-6 gap-1 overflow-hidden">
      {cells.map((c, i) => (
        <div key={i} className="px-4 py-3 rounded-xl bg-obsidian/40 border border-white/5">
          <div className="text-[10px] uppercase tracking-wider text-sage">{c.label}</div>
          <div className="font-display text-pearl mt-1 flex items-center gap-2">
            <i className={`dot dot-${c.tone}`}></i>{c.val}
          </div>
        </div>
      ))}
    </div>
  );
}
"""

F["components/WeatherRiskOrb.tsx"] = r"""export function WeatherRiskOrb({ label = "Mixed rainfall", level = "moderate" }: { label?: string; level?: "low"|"moderate"|"high" }) {
  const color = level === "high" ? "#D65A46" : level === "moderate" ? "#F2B84B" : "#39D98A";
  return (
    <div className="panel p-5 lift">
      <div className="text-[10px] uppercase tracking-wider text-sage">Weather risk</div>
      <div className="flex items-center gap-4 mt-3">
        <div className="relative h-20 w-20 rounded-full grid place-items-center"
          style={{ background: `radial-gradient(circle at 30% 30%, ${color}33, transparent 70%), conic-gradient(${color}66, transparent 70%)` }}>
          <div className="absolute inset-2 rounded-full bg-obsidian border border-white/10 grid place-items-center font-display text-pearl">
            {level === "high" ? "H" : level === "moderate" ? "M" : "L"}
          </div>
        </div>
        <div>
          <div className="font-display text-pearl text-lg">{label}</div>
          <div className="text-sage text-xs mt-1">Next 7-day forecast</div>
        </div>
      </div>
    </div>
  );
}
"""

F["components/VerdictCapsule.tsx"] = r"""import { ConsensusBadge, RiskBadge, ActionWindowBadge } from "./Badges";
import { HashText } from "./HashText";

export function VerdictCapsule({ v }: { v: any }) {
  if (!v) {
    return (
      <div className="panel p-6 relative scanline">
        <div className="text-[10px] uppercase tracking-wider text-sage">Latest verdict</div>
        <div className="font-display text-2xl text-pearl/60 mt-2">No advisory yet</div>
        <div className="text-sage text-sm mt-1">Submit your first case to GenLayer to see a consensus verdict.</div>
      </div>
    );
  }
  return (
    <div className="panel-violet p-6 relative scanline lift">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Consensus verdict</div>
        <ConsensusBadge label={v.consensus_status ?? "Validated"} />
      </div>
      <div className="font-display text-4xl text-pearl mt-3">{v.verdict}</div>
      <div className="flex flex-wrap gap-2 mt-3">
        {v.risk_level && <RiskBadge level={v.risk_level} />}
        <ActionWindowBadge window={"Review window 5d"} />
        <span className="badge badge-bio">{v.confidence_label ?? "Strong"} confidence</span>
      </div>
      {v.reasoning_summary && (
        <p className="text-sm text-pearl/80 mt-4 leading-relaxed">{v.reasoning_summary}</p>
      )}
      <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-4">
        <HashText label="tx" value={v.transaction_hash} />
        <HashText label="contract" value={v.contract_address} />
        <HashText label="digest" value={v.evidence_digest} />
      </div>
    </div>
  );
}
"""

F["components/GenLayerConsensusPanel.tsx"] = r"""import { ConsensusBadge, SourceOfTruthBadge } from "./Badges";
import { HashText } from "./HashText";

export function GenLayerConsensusPanel({ v }: { v: any }) {
  return (
    <div className="panel p-6 relative scanline">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer Adjudication</div>
          <div className="font-display text-pearl text-xl mt-1">Consensus module</div>
        </div>
        <SourceOfTruthBadge />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-5 text-sm">
        <div><div className="text-[10px] uppercase text-sage">Network</div><div className="text-pearl">StudioNet</div></div>
        <div><div className="text-[10px] uppercase text-sage">Status</div><div><ConsensusBadge label={v?.consensus_status ?? "—"} /></div></div>
        <div><div className="text-[10px] uppercase text-sage">Contract</div><HashText value={v?.contract_address} /></div>
        <div><div className="text-[10px] uppercase text-sage">Advisory ID</div><HashText value={v?.advisory_id_on_chain} /></div>
        <div className="col-span-2"><div className="text-[10px] uppercase text-sage">Transaction</div><HashText value={v?.transaction_hash} /></div>
      </div>
    </div>
  );
}
"""

F["components/EvidenceStrengthMeter.tsx"] = r"""export function EvidenceStrengthMeter({ score = 60 }: { score?: number }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="panel p-5">
      <div className="text-[10px] uppercase tracking-wider text-sage">Evidence strength</div>
      <div className="font-display text-3xl text-pearl mt-2">{pct}%</div>
      <div className="mt-3 h-2 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "linear-gradient(90deg,#39D98A,#00C2B8)" }} />
      </div>
      <div className="text-xs text-sage mt-2">Soil · Weather · Market · Uploaded files</div>
    </div>
  );
}
"""

F["components/CropWindowTimeline.tsx"] = r"""export function CropWindowTimeline() {
  const days = Array.from({ length: 14 }, (_, i) => i + 1);
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Crop window — 14 days</div>
        <span className="badge badge-gold">Caution window</span>
      </div>
      <div className="mt-3 grid grid-cols-14 gap-1">
        {days.map(d => {
          const tone =
            d <= 4 ? "bg-stormclay/60"
            : d <= 7 ? "bg-yieldgold/60"
            : "bg-biosignal/60";
          return (
            <div key={d} className="flex flex-col items-center gap-1">
              <div className={`w-full h-10 rounded-md ${tone}`}></div>
              <div className="text-[10px] text-sage">{d}</div>
            </div>
          );
        })}
      </div>
      <style>{`.grid-cols-14{grid-template-columns:repeat(14,minmax(0,1fr));}`}</style>
    </div>
  );
}
"""

F["components/ContractActivityStream.tsx"] = r"""import { HashText } from "./HashText";

export function ContractActivityStream({ items }: { items: any[] }) {
  if (!items?.length)
    return <div className="panel p-5 text-sage text-sm">No contract activity yet. Submitting a case will log GenLayer interaction here.</div>;
  return (
    <div className="panel p-5">
      <div className="text-[10px] uppercase tracking-wider text-sage">Contract activity stream</div>
      <ul className="mt-3 space-y-3">
        {items.map((a, i) => (
          <li key={i} className="flex items-start gap-3">
            <i className={`dot mt-1.5 ${a.status === "error" ? "dot-risk" : a.status === "submitted" ? "dot-sensor" : "dot-bio"}`}></i>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-pearl">{a.action} · <span className="text-sage">{a.status}</span></div>
              <div className="text-xs text-sage mt-1 flex flex-wrap gap-3">
                <HashText label="tx" value={a.transaction_hash} />
                <span>{new Date(a.created_at).toLocaleString()}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
"""

F["components/EvidenceVaultCard.tsx"] = r"""import { HashText } from "./HashText";

export function EvidenceVaultCard({ f }: { f: any }) {
  const type = (f.file_type || "").split("/").pop()?.toUpperCase();
  return (
    <div className="panel p-5 lift">
      <div className="flex items-center justify-between">
        <span className="badge badge-muted">{type ?? "FILE"}</span>
        <span className="badge badge-bio">In vault</span>
      </div>
      <div className="font-mono text-xs mt-3 break-all text-pearl/80">{f.file_path}</div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
        <div><div className="text-[10px] uppercase text-sage">Size</div><div className="text-pearl">{(f.file_size/1024).toFixed(1)} KB</div></div>
        <div><div className="text-[10px] uppercase text-sage">Uploaded</div><div className="text-pearl">{new Date(f.created_at).toLocaleDateString()}</div></div>
      </div>
      <div className="mt-3"><HashText label="sha256" value={f.evidence_hash} /></div>
    </div>
  );
}
"""

F["components/RecoveryKeyPanel.tsx"] = r""""use client";
import { useState } from "react";
export function RecoveryKeyPanel({ recoveryKey }: { recoveryKey: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="panel-pollen p-6 mt-6 relative">
      <div className="flex items-center justify-between">
        <span className="badge badge-gold">One-time secret</span>
        <span className="text-[10px] uppercase tracking-wider text-soil/60">Save offline</span>
      </div>
      <h3 className="font-display text-2xl text-soil mt-3">Your recovery key</h3>
      <p className="text-sm text-soil/70 mt-1">
        This restores access to your embedded wallet if you forget your password. It is shown only once. Treat it like a hardware seed.
      </p>
      <div className="mt-3 font-mono text-lg p-4 bg-white rounded-xl border border-reed break-all">{recoveryKey}</div>
      <button className="btn-primary mt-3"
        onClick={() => { navigator.clipboard.writeText(recoveryKey); setCopied(true); }}>
        {copied ? "Copied" : "Copy key"}
      </button>
    </div>
  );
}
"""

F["components/AdvisoryPacketRails.tsx"] = r"""import { HashText } from "./HashText";
import { ConsensusBadge } from "./Badges";

export function LeftPacketRail({ farms, c }: { farms: any[]; c?: any }) {
  return (
    <aside className="panel p-5 sticky top-24">
      <div className="text-[10px] uppercase tracking-wider text-sage">Advisory packet</div>
      <div className="mt-4 space-y-3 text-sm">
        <Row k="Farms available" v={`${farms.length}`} />
        <Row k="Crop" v={c?.crop_type ?? "—"} />
        <Row k="Decision" v={c?.decision_type ?? "—"} />
        <Row k="Status" v={c?.status ?? "draft"} />
      </div>
      <div className="hr my-4" />
      <div className="text-[10px] uppercase tracking-wider text-sage">Readiness</div>
      <div className="mt-2 h-2 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full" style={{ width: c ? "70%" : "30%", background: "linear-gradient(90deg,#39D98A,#00C2B8)" }} />
      </div>
    </aside>
  );
}

export function RightPacketRail({ verdict }: { verdict?: any }) {
  return (
    <aside className="panel-violet p-5 sticky top-24 relative scanline">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer readiness</div>
        <ConsensusBadge label="Awaiting submission" />
      </div>
      <p className="text-sm text-pearl/80 mt-3">
        AgroSense prepares the advisory packet. The final verdict is produced by independent
        GenLayer validators reaching consensus on the most defensible action.
      </p>
      <div className="hr my-4" />
      <div className="text-[10px] uppercase tracking-wider text-sage">Mirrored verdict</div>
      <div className="mt-2 text-sm text-pearl">{verdict?.verdict ?? "Not yet issued"}</div>
      {verdict && <div className="mt-2"><HashText label="tx" value={verdict.transaction_hash} /></div>}
    </aside>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sage text-xs uppercase tracking-wider">{k}</span>
      <span className="text-pearl text-sm font-display truncate max-w-[55%] text-right">{v}</span>
    </div>
  );
}
"""

# =========================================================================
#                              LAYOUT
# =========================================================================

F["app/layout.tsx"] = r"""import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgroSense — Field Intelligence OS",
  description:
    "Field Intelligence OS for farm decisions. Consensus-backed advisory verdicts powered by GenLayer.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
"""

# =========================================================================
#                              LANDING
# =========================================================================

F["app/page.tsx"] = r"""import Link from "next/link";
import { Brand } from "@/components/Brand";
import { ConsensusBadge, LiveBadge, RiskBadge, ActionWindowBadge } from "@/components/Badges";
import { AGROSENSE_CONTRACT_ADDRESS, AGROSENSE_CONTRACT_NETWORK } from "@/lib/genlayer/contract";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-field-grid">
      <nav className="max-w-7xl mx-auto flex items-center justify-between px-6 py-5">
        <Brand />
        <div className="flex items-center gap-3">
          <LiveBadge label="StudioNet · Live" />
          <Link href="/login" className="btn-ghost text-sm">Log in</Link>
          <Link href="/signup" className="btn-primary text-sm">Create account</Link>
        </div>
      </nav>

      {/* HERO */}
      <section className="max-w-7xl mx-auto px-6 pt-10 pb-20 grid lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7">
          <span className="badge badge-consensus">GenLayer · Field Intelligence OS</span>
          <h1 className="font-display text-5xl md:text-7xl font-bold text-pearl mt-5 leading-[1.05] tracking-tight">
            The farm decision layer<br/>
            powered by <span className="text-biosignal">consensus</span>.
          </h1>
          <p className="mt-6 text-lg text-sage max-w-xl leading-relaxed">
            Turn uncertain planting, irrigation, harvest, and risk decisions into GenLayer
            consensus-backed advisory verdicts. AgroSense prepares the case — independent
            validators issue the verdict.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup" className="btn-primary">+ Create advisory case</Link>
            <Link href="/demo"   className="btn-ghost">View demo verdict →</Link>
          </div>
          <div className="mt-10 flex items-center gap-6 text-xs text-sage">
            <span className="flex items-center gap-2"><i className="dot dot-bio"></i>Embedded wallet</span>
            <span className="flex items-center gap-2"><i className="dot dot-sensor"></i>Live data</span>
            <span className="flex items-center gap-2"><i className="dot dot-violet"></i>Validator consensus</span>
          </div>
        </div>

        {/* Hero terminal */}
        <div className="lg:col-span-5">
          <div className="panel-violet p-6 relative scanline">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-sage">ADVISORY · KADUNA-NORTH-001</span>
              <ConsensusBadge />
            </div>
            <div className="mt-4">
              <div className="text-[10px] uppercase tracking-wider text-sage">Verdict</div>
              <div className="font-display text-4xl text-pearl font-bold">Delay planting</div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-5">
              <Field k="Crop" v="Maize" />
              <Field k="Region" v="Kaduna North" />
              <Field k="Weather" v="Mixed rainfall" tone="sensor" />
              <Field k="Soil report" v="Incomplete" tone="gold" />
              <Field k="Market" v="Positive" tone="bio" />
              <Field k="GenLayer" v="Consensus reached" tone="violet" />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <RiskBadge level="High rainfall" />
              <ActionWindowBadge window="Review in 5 days" />
            </div>
            <div className="mt-5 pt-4 border-t border-white/10 text-[11px] font-mono text-sage break-all">
              {AGROSENSE_CONTRACT_NETWORK} · {AGROSENSE_CONTRACT_ADDRESS}
            </div>
          </div>
        </div>
      </section>

      {/* Why not ordinary AI */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-[11px] uppercase tracking-[0.2em] text-sage">Why this is not ordinary AI advice</div>
        <h2 className="font-display text-4xl text-pearl mt-3">One question. Three approaches.</h2>
        <div className="grid md:grid-cols-3 gap-5 mt-8">
          <Compare
            tag="Normal AI tool" tagTone="muted"
            title="One private recommendation"
            body="A single black-box model gives one answer. No second opinion. No proof of reasoning. No way to know if a different model would disagree."
          />
          <Compare
            tag="Threshold app" tagTone="gold"
            title="Fixed weather rules"
            body="If rainfall > X, plant. Predictable, brittle, blind to context. Cannot weigh competing signals like market, soil, and observation together."
          />
          <Compare
            tag="AgroSense" tagTone="violet" highlight
            title="Validator consensus"
            body="The advisory packet is submitted to a GenLayer Intelligent Contract. Independent validators reason over the evidence and converge on the most defensible action."
          />
        </div>
      </section>

      {/* Capabilities */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-4 gap-4">
          {[
            ["Embedded wallet", "Auto-created at signup. Permanent. Used silently for GenLayer signing."],
            ["Evidence vault",  "Soil PDFs, farm imagery, market screenshots — hashed and submitted by reference."],
            ["Consensus verdict", "Validators issue the verdict. AgroSense never decides."],
            ["Audit trail",     "Every advisory case mirrors its on-chain result, hash, and transaction."],
          ].map(([t, d]) => (
            <div key={t} className="panel p-5">
              <div className="text-pearl font-display text-lg">{t}</div>
              <div className="text-sage text-sm mt-2 leading-relaxed">{d}</div>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/5 mt-10">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-wrap justify-between gap-3 text-xs text-sage">
          <span>© AgroSense — Field Intelligence OS</span>
          <span className="font-mono">{AGROSENSE_CONTRACT_NETWORK} · {AGROSENSE_CONTRACT_ADDRESS}</span>
        </div>
      </footer>
    </main>
  );
}

function Field({ k, v, tone }: { k: string; v: string; tone?: "bio"|"sensor"|"gold"|"violet" }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-sage">{k}</div>
      <div className="text-pearl font-display flex items-center gap-2 mt-1">
        {tone && <i className={`dot dot-${tone}`}></i>}{v}
      </div>
    </div>
  );
}

function Compare({ tag, tagTone, title, body, highlight }: { tag: string; tagTone: "muted"|"gold"|"violet"; title: string; body: string; highlight?: boolean }) {
  return (
    <div className={`panel p-6 ${highlight ? "ring-1 ring-consensus/40 shadow-violet" : ""}`}>
      <span className={`badge badge-${tagTone === "muted" ? "muted" : tagTone === "gold" ? "gold" : "consensus"}`}>{tag}</span>
      <div className="font-display text-pearl text-xl mt-3">{title}</div>
      <p className="text-sage text-sm mt-3 leading-relaxed">{body}</p>
    </div>
  );
}
"""

# =========================================================================
#                                AUTH
# =========================================================================

def auth_left():
    return r"""
      <aside className="hidden md:flex flex-col justify-between p-10 bg-graphite/60 border-r border-white/5 relative overflow-hidden">
        <div className="relative z-10"><Brand size="lg" /></div>
        <div className="relative z-10 max-w-md">
          <span className="badge badge-consensus">Field Intelligence OS</span>
          <h2 className="font-display text-4xl text-pearl mt-4 leading-tight">Consensus-backed farm decisions begin at the access terminal.</h2>
          <p className="text-sage mt-4 leading-relaxed">
            Your AgroSense profile includes a secure embedded wallet used only for GenLayer
            actions. You do not need MetaMask, Rabby, Rainbow, or Zerion for normal use.
          </p>
        </div>
        <div className="relative z-10 flex gap-3">
          <span className="badge badge-bio"><i className="dot dot-bio"></i>Embedded wallet</span>
          <span className="badge badge-sensor"><i className="dot dot-sensor"></i>Live signals</span>
          <span className="badge badge-consensus"><i className="dot dot-violet"></i>Validator consensus</span>
        </div>
        <div className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full opacity-30"
          style={{ background: "radial-gradient(circle, rgba(57,217,138,0.35), transparent 60%)" }} />
        <div className="absolute -top-32 -left-20 w-80 h-80 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.35), transparent 60%)" }} />
      </aside>"""

F["app/signup/page.tsx"] = r""""use client";
import { useState } from "react";
import Link from "next/link";
import { signUp } from "@/server/actions/auth";
import { RecoveryKeyPanel } from "@/components/RecoveryKeyPanel";
import { Brand } from "@/components/Brand";

export default function SignupPage() {
  const [err, setErr] = useState<string>();
  const [recoveryKey, setRecoveryKey] = useState<string>();

  async function action(fd: FormData) {
    const r = await signUp(fd);
    if (!r.ok) setErr(r.error); else setRecoveryKey(r.recoveryKey);
  }

  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-field-grid">""" + auth_left() + r"""
      <section className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {!recoveryKey ? (
            <>
              <span className="badge badge-bio">Access terminal · Signup</span>
              <h1 className="font-display text-4xl text-pearl mt-3">Create your operator profile</h1>
              <p className="text-sage text-sm mt-2">A secure embedded wallet is created automatically and linked to your profile.</p>
              <form action={action} className="panel p-6 mt-6 space-y-3">
                <label className="text-[10px] uppercase tracking-wider text-sage">Email</label>
                <input name="email" type="email" required className="input" placeholder="operator@farm.org" />
                <label className="text-[10px] uppercase tracking-wider text-sage">Password</label>
                <input name="password" type="password" required minLength={8} className="input" placeholder="Minimum 8 characters" />
                <button className="btn-primary w-full mt-2" type="submit">Initialise profile</button>
                {err && <p className="text-stormclay text-sm mt-1">{err}</p>}
              </form>
              <p className="text-sm text-sage mt-4">Already have an account? <Link href="/login" className="text-biosignal">Log in</Link></p>
            </>
          ) : (
            <>
              <span className="badge badge-consensus">Operator initialised</span>
              <h1 className="font-display text-4xl text-pearl mt-3">Wallet attached</h1>
              <RecoveryKeyPanel recoveryKey={recoveryKey} />
              <Link href="/login" className="btn-primary mt-6 inline-block">Continue to access terminal</Link>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
"""

F["app/login/page.tsx"] = r""""use client";
import { useState } from "react";
import Link from "next/link";
import { logIn } from "@/server/actions/auth";
import { Brand } from "@/components/Brand";

export default function LoginPage() {
  const [err, setErr] = useState<string>();
  async function action(fd: FormData) {
    const r = (await logIn(fd)) as any;
    if (r && !r.ok) setErr(r.error);
  }
  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-field-grid">""" + auth_left() + r"""
      <section className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <span className="badge badge-sensor">Access terminal</span>
          <h1 className="font-display text-4xl text-pearl mt-3">Operator log-in</h1>
          <p className="text-sage text-sm mt-2">Email and password. No external wallet required.</p>
          <form action={action} className="panel p-6 mt-6 space-y-3">
            <label className="text-[10px] uppercase tracking-wider text-sage">Email</label>
            <input name="email" type="email" required className="input" placeholder="operator@farm.org" />
            <label className="text-[10px] uppercase tracking-wider text-sage">Password</label>
            <input name="password" type="password" required className="input" />
            <button className="btn-primary w-full mt-2" type="submit">Continue</button>
            {err && <p className="text-stormclay text-sm mt-1">{err}</p>}
          </form>
          <div className="flex justify-between text-sm text-sage mt-4">
            <Link href="/forgot-password" className="text-biosignal">Forgot password</Link>
            <Link href="/signup" className="text-biosignal">Create account</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
"""

F["app/forgot-password/page.tsx"] = r"""import Link from "next/link";
import { Brand } from "@/components/Brand";

export default function P() {
  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-field-grid">""" + auth_left() + r"""
      <section className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <span className="badge badge-gold">Recovery</span>
          <h1 className="font-display text-4xl text-pearl mt-3">Lost password?</h1>
          <p className="text-sage mt-3">Use your recovery key to set a new password. Your embedded wallet stays the same — only the password wrap is replaced.</p>
          <Link href="/reset-password" className="btn-primary inline-block mt-6">Use recovery key →</Link>
        </div>
      </section>
    </main>
  );
}
"""

F["app/reset-password/page.tsx"] = r""""use client";
import { useState } from "react";
import { recoverWithKey } from "@/server/actions/auth";
import { Brand } from "@/components/Brand";

export default function ResetPasswordPage() {
  const [msg, setMsg] = useState<string>();
  const [err, setErr] = useState<string>();
  async function action(fd: FormData) {
    const r = await recoverWithKey(fd);
    if (r.ok) setMsg("Password reset. Your wallet was preserved. You can log in now.");
    else setErr(r.error);
  }
  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-field-grid">""" + auth_left() + r"""
      <section className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <span className="badge badge-gold">Recovery flow</span>
          <h1 className="font-display text-4xl text-pearl mt-3">Recover with key</h1>
          <p className="text-sage text-sm mt-2">Your wallet address never changes. Only the password wrap is replaced.</p>
          <form action={action} className="panel p-6 mt-6 space-y-3">
            <input name="email" type="email" required className="input" placeholder="Email" />
            <input name="recoveryKey" required className="input font-mono" placeholder="Recovery key (xxxx-xxxx-xxxx)" />
            <input name="newPassword" type="password" required minLength={8} className="input" placeholder="New password" />
            <button className="btn-primary w-full mt-2">Recover & re-wrap wallet</button>
            {err && <p className="text-stormclay text-sm">{err}</p>}
            {msg && <p className="text-biosignal text-sm">{msg}</p>}
          </form>
        </div>
      </section>
    </main>
  );
}
"""

# =========================================================================
#                          ONBOARDING
# =========================================================================

F["app/onboarding/page.tsx"] = r"""import Link from "next/link";
import { AppShell } from "@/components/AppShell";

const stages = [
  ["01", "Farm identity",        "Name, country, region — anchor the case to a real plot."],
  ["02", "Location intelligence", "Coordinates and nearest town drive weather and risk signals."],
  ["03", "Crop focus",            "Primary crops decide which advisory plans validators compare."],
  ["04", "Soil & irrigation",     "Soil type and irrigation availability calibrate evidence quality."],
  ["05", "Evidence readiness",    "Have soil PDFs and farm images ready before opening an advisory case."],
  ["06", "Recovery key",          "You already saved one at signup. Re-confirm it lives offline."],
];

export default async function OnboardingPage() {
  return (
    <AppShell section="Field Intelligence Setup" subtitle="Six-stage operator onboarding">
      <div className="max-w-5xl mx-auto">
        <span className="badge badge-bio">Setup</span>
        <h1 className="font-display text-4xl text-pearl mt-3">Calibrate AgroSense for your fields</h1>
        <p className="text-sage mt-3 max-w-2xl">
          AgroSense behaves like an OS — better calibration produces stronger advisory packets,
          and stronger packets produce more defensible GenLayer verdicts.
        </p>

        <div className="grid md:grid-cols-2 gap-4 mt-8">
          {stages.map(([n, t, d]) => (
            <div key={n} className="panel p-5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] text-sage">STAGE {n}</span>
                <i className="dot dot-sensor"></i>
              </div>
              <div className="font-display text-pearl text-xl mt-2">{t}</div>
              <p className="text-sage text-sm mt-2 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>

        <div className="panel-violet p-6 mt-8 relative scanline">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-sage">Next step</div>
              <div className="font-display text-2xl text-pearl mt-1">Add your first farm</div>
            </div>
            <Link className="btn-primary" href="/farms">Open farm profiles →</Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
"""

# =========================================================================
#                          DASHBOARD
# =========================================================================

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

        {/* Hero row */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-7"><VerdictCapsule v={latest} /></div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-2"><WeatherRiskOrb level="moderate" label="Mixed rainfall" /></div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-3"><GenLayerConsensusPanel v={latest} /></div>
        </div>

        {/* Second row */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8">
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between px-5 pt-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-sage">Active case matrix</div>
                  <div className="font-display text-pearl text-lg">Recent advisories</div>
                </div>
                <Link href="/cases/new" className="btn-primary text-sm">+ New case</Link>
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

        {/* Third row */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><CropWindowTimeline /></div>
          <div className="col-span-12 lg:col-span-4"><ContractActivityStream items={activity ?? []} /></div>
        </div>

        {/* Notes */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-6 panel p-5">
            <div className="text-[10px] uppercase tracking-wider text-sage">Market signal</div>
            <div className="font-display text-2xl text-pearl mt-1">Maize +9% MoM</div>
            <p className="text-sage text-sm mt-2">Demo data. Replace with real market snapshots when integrating market API.</p>
          </div>
          <div className="col-span-12 lg:col-span-6 panel p-5">
            <div className="text-[10px] uppercase tracking-wider text-sage">Field notes</div>
            <p className="text-pearl/80 text-sm mt-2">Attach evidence early. Stronger packets produce more defensible verdicts.</p>
            <div className="mt-3"><LiveBadge label="Network synced" /></div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
"""

# =========================================================================
#                                FARMS
# =========================================================================

F["app/farms/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { createFarm } from "@/server/actions/farms";

export default async function FarmsPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farms } = await sb.from("farms").select("*").eq("user_id", me.user!.id).order("created_at", { ascending: false });

  return (
    <AppShell section="Farm registry" subtitle="Plots, crops, irrigation, coordinates">
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="font-display text-3xl text-pearl">Your farms</h1>
            <span className="badge badge-muted">{farms?.length ?? 0} registered</span>
          </div>
          {(farms ?? []).length === 0 && (
            <div className="panel p-10 text-center text-sage">No farms yet. Add your first farm to start advisory cases.</div>
          )}
          {(farms ?? []).map(f => (
            <div key={f.id} className="panel p-5 lift">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-display text-pearl text-xl">{f.name}</div>
                  <div className="text-sage text-sm">{f.region ? `${f.region}, ` : ""}{f.country}{f.nearest_town ? ` · ${f.nearest_town}` : ""}</div>
                </div>
                <span className="badge badge-bio">Active</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-sm">
                <Cell k="Size" v={f.farm_size ? `${f.farm_size} ha` : "—"} />
                <Cell k="Soil" v={f.soil_type ?? "—"} />
                <Cell k="Irrigation" v={f.irrigation_available ? "Yes" : "No"} />
                <Cell k="Crops" v={f.main_crops?.length ? f.main_crops.join(", ") : "—"} />
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-12 lg:col-span-5">
          <div className="panel-ivory p-6 light-surface">
            <span className="badge badge-bio">Add farm</span>
            <h2 className="font-display text-2xl text-soil mt-2">Register a new plot</h2>
            <p className="text-soil/60 text-sm mt-1">Used to anchor advisory cases and signal context.</p>
            <form action={createFarm} className="space-y-3 mt-5">
              <input name="name" required placeholder="Farm name" className="input-light" />
              <div className="grid grid-cols-2 gap-3">
                <input name="country" required placeholder="Country" className="input-light" />
                <input name="region" placeholder="State / region" className="input-light" />
              </div>
              <input name="nearestTown" placeholder="Nearest town" className="input-light" />
              <div className="grid grid-cols-2 gap-3">
                <input name="latitude"  type="number" step="any" placeholder="Latitude"  className="input-light" />
                <input name="longitude" type="number" step="any" placeholder="Longitude" className="input-light" />
              </div>
              <input name="farmSize" type="number" step="any" placeholder="Farm size (ha)" className="input-light" />
              <input name="soilType" placeholder="Soil type" className="input-light" />
              <input name="mainCrops" placeholder="Main crops (comma separated)" className="input-light" />
              <label className="flex items-center gap-2 text-sm text-soil">
                <input name="irrigationAvailable" type="checkbox" /> Irrigation available
              </label>
              <input name="previousPlantingDate" type="date" className="input-light" />
              <button className="btn-primary w-full">Register farm</button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Cell({ k, v }: { k: string; v: string }) {
  return <div><div className="text-[10px] uppercase text-sage">{k}</div><div className="text-pearl mt-1">{v}</div></div>;
}
"""

# =========================================================================
#                          CREATE ADVISORY CASE
# =========================================================================

F["app/cases/new/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { createAdvisoryCase } from "@/server/actions/cases";
import { LeftPacketRail, RightPacketRail } from "@/components/AdvisoryPacketRails";
import { ConsensusBadge } from "@/components/Badges";

export default async function NewCasePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farms } = await sb.from("farms").select("id,name,country,region").eq("user_id", me.user!.id);

  return (
    <AppShell section="Advisory Packet Builder" subtitle="Assemble the intelligence packet for GenLayer adjudication">
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-3 hidden lg:block"><LeftPacketRail farms={farms ?? []} /></div>

        <div className="col-span-12 lg:col-span-6 space-y-5">
          <Step n="01" t="Select farm & decision">
            <form action={createAdvisoryCase} className="space-y-3">
              <label className="text-[10px] uppercase tracking-wider text-sage">Farm</label>
              <select name="farmId" required className="input">
                {(farms ?? []).map(f => <option key={f.id} value={f.id}>{f.name} ({f.region ?? ""}, {f.country})</option>)}
              </select>

              <label className="text-[10px] uppercase tracking-wider text-sage">Decision type</label>
              <select name="decisionType" required className="input">
                <option value="plant_now">Should I plant now?</option>
                <option value="delay_planting">Should I delay planting?</option>
                <option value="irrigate">Should I irrigate?</option>
                <option value="harvest_window">Is this harvest window safe?</option>
                <option value="risk_check">Is this farm action too risky?</option>
              </select>

              <label className="text-[10px] uppercase tracking-wider text-sage">Crop</label>
              <input name="cropType" required placeholder="Maize, rice, cassava…" className="input" />

              <label className="text-[10px] uppercase tracking-wider text-sage">Advisory question</label>
              <input name="advisoryQuestion" required className="input" placeholder="Should I plant maize this week?" />

              <label className="text-[10px] uppercase tracking-wider text-sage">Decision window</label>
              <input name="plantingWindow" className="input" placeholder="Next 7–14 days" />

              <div className="grid grid-cols-1 gap-3 pt-2">
                <label className="text-[10px] uppercase tracking-wider text-sage">Field observation</label>
                <textarea name="userObservation" rows={3} className="input" placeholder="What you can see from the field right now" />
                <label className="text-[10px] uppercase tracking-wider text-sage">Weather context</label>
                <textarea name="weatherContext" rows={3} className="input" placeholder="Forecast notes (rain probability, temperature)" />
                <label className="text-[10px] uppercase tracking-wider text-sage">Market context (optional)</label>
                <textarea name="marketContext" rows={2} className="input" placeholder="Price trend, demand signal" />
              </div>

              <button className="btn-primary w-full mt-3">Save draft & continue →</button>
              <p className="text-xs text-sage">You can attach up to 3 evidence files on the next step before submitting to GenLayer.</p>
            </form>
          </Step>

          <div className="panel-violet p-6 relative scanline">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer Review</div>
                <div className="font-display text-pearl text-xl mt-1">Validator consensus</div>
              </div>
              <ConsensusBadge label="Source of truth" />
            </div>
            <p className="text-pearl/80 text-sm mt-3 leading-relaxed">
              This case will be evaluated by GenLayer validators. AgroSense prepares the advisory
              packet, but the final verdict is not produced by the frontend, Supabase, or any
              private backend. Validators independently reason over the evidence and reach
              consensus on the most defensible advisory outcome.
            </p>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 hidden lg:block"><RightPacketRail /></div>
      </div>
    </AppShell>
  );
}

function Step({ n, t, children }: { n: string; t: string; children: React.ReactNode }) {
  return (
    <section className="panel p-6">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs text-sage">STEP {n}</span>
        <div className="font-display text-pearl text-xl">{t}</div>
      </div>
      <div className="hr my-4" />
      {children}
    </section>
  );
}
"""

# =========================================================================
#                          CASE DETAIL / VERDICT
# =========================================================================

F["app/cases/[id]/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { submitToGenLayer } from "@/server/actions/cases";
import { uploadEvidence } from "@/server/actions/evidence";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { HashText } from "@/components/HashText";
import { ConsensusBadge } from "@/components/Badges";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: c } = await sb.from("advisory_cases")
    .select("*, farms(name,country,region)").eq("id", id).eq("user_id", me.user!.id).maybeSingle();
  if (!c) redirect("/dashboard");
  const { data: ev } = await sb.from("evidence_files").select("*").eq("advisory_case_id", id);
  const { data: verdict } = await sb.from("genlayer_verdicts")
    .select("*").eq("advisory_case_id", id).order("created_at", { ascending: false }).maybeSingle();

  async function submit() { "use server"; await submitToGenLayer(id); }

  return (
    <AppShell section={verdict ? "Consensus Verdict Terminal" : "Advisory Packet Builder"} subtitle={`${c.crop_type} · ${c.decision_type}`}>
      <div className="space-y-6">
        {/* HERO */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><VerdictCapsule v={verdict} /></div>
          <div className="col-span-12 lg:col-span-4"><GenLayerConsensusPanel v={verdict} /></div>
        </div>

        {/* CASE BODY */}
        <div className="grid grid-cols-12 gap-5">
          <section className="col-span-12 lg:col-span-5 panel p-5">
            <div className="text-[10px] uppercase tracking-wider text-sage">Advisory question</div>
            <p className="text-pearl mt-2 leading-relaxed">{c.advisory_question}</p>
            <div className="hr my-4" />
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Cell k="Farm"   v={(c as any).farms?.name ?? "—"} />
              <Cell k="Region" v={`${(c as any).farms?.region ?? ""} ${(c as any).farms?.country ?? ""}`} />
              <Cell k="Crop"   v={c.crop_type} />
              <Cell k="Window" v={c.planting_window ?? "—"} />
            </div>
            {c.user_observation && (
              <>
                <div className="hr my-4" />
                <div className="text-[10px] uppercase tracking-wider text-sage">Field observation</div>
                <p className="text-pearl/80 text-sm mt-2 leading-relaxed">{c.user_observation}</p>
              </>
            )}
          </section>

          <section className="col-span-12 lg:col-span-4 panel p-5">
            <div className="flex items-center justify-between">
              <div className="text-[10px] uppercase tracking-wider text-sage">Evidence vault</div>
              <span className="badge badge-muted">{ev?.length ?? 0} / 3</span>
            </div>
            <ul className="mt-3 space-y-2">
              {(ev ?? []).map(e => (
                <li key={e.id} className="rounded-xl border border-white/5 bg-obsidian/40 p-3">
                  <div className="font-mono text-[11px] text-pearl/80 break-all">{e.file_path}</div>
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    <span className="badge badge-muted">{e.file_type.split("/").pop()?.toUpperCase()}</span>
                    <HashText label="sha256" value={e.evidence_hash} />
                  </div>
                </li>
              ))}
            </ul>
            {(ev?.length ?? 0) < 3 && (
              <form action={uploadEvidence} encType="multipart/form-data" className="mt-3 flex flex-col gap-2">
                <input type="hidden" name="caseId" value={id} />
                <input type="file" name="file" required accept=".jpg,.jpeg,.png,.webp,.pdf,.json" className="text-sm text-sage file:btn-ghost file:mr-3 file:bg-white/5 file:border file:border-white/10 file:rounded-lg file:text-pearl" />
                <button className="btn-ghost">Attach evidence</button>
              </form>
            )}
          </section>

          <section className="col-span-12 lg:col-span-3 panel-violet p-5 relative scanline">
            <div className="text-[10px] uppercase tracking-wider text-sage">Adjudication</div>
            <div className="font-display text-pearl text-xl mt-1">GenLayer submit</div>
            <p className="text-sage text-xs mt-2">When ready, the advisory packet is sent to the AgroSenseAdvisory contract. The verdict is produced by validator consensus.</p>
            {!verdict ? (
              <form action={submit} className="mt-4"><button className="btn-violet w-full">Submit to GenLayer →</button></form>
            ) : (
              <div className="mt-4"><ConsensusBadge label="Verdict issued" /></div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}

function Cell({ k, v }: { k: string; v: string }) {
  return <div><div className="text-[10px] uppercase text-sage">{k}</div><div className="text-pearl mt-1">{v}</div></div>;
}
"""

# =========================================================================
#                          EVIDENCE ROOM
# =========================================================================

F["app/evidence/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { EvidenceVaultCard } from "@/components/EvidenceVaultCard";

export default async function EvidenceRoom() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: ev } = await sb.from("evidence_files")
    .select("*").eq("user_id", me.user!.id).order("created_at", { ascending: false });

  return (
    <AppShell section="Evidence vault" subtitle="Hashed soil reports, imagery, snapshots">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-pearl">All evidence</h1>
          <p className="text-sage text-sm mt-1">Each item is hashed and referenced by digest in the GenLayer advisory packet.</p>
        </div>
        <span className="badge badge-muted">{ev?.length ?? 0} items</span>
      </div>

      {(ev ?? []).length === 0 ? (
        <div className="panel p-10 text-center text-sage mt-6">No evidence yet. Upload from a case to populate the vault.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
          {ev!.map(f => <EvidenceVaultCard key={f.id} f={f} />)}
        </div>
      )}
    </AppShell>
  );
}
"""

# =========================================================================
#                          ADMIN CONSOLE
# =========================================================================

F["app/admin/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";
import { ConsensusBadge } from "@/components/Badges";
import { AGROSENSE_CONTRACT_ADDRESS, AGROSENSE_CONTRACT_NETWORK } from "@/lib/genlayer/contract";

export default async function AdminPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user!.id).maybeSingle();
  if (prof?.role !== "admin") redirect("/dashboard");

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,user_id,crop_type,status,created_at").order("created_at", { ascending: false }).limit(50);
  const { data: verdicts } = await sb.from("genlayer_verdicts")
    .select("*").order("created_at", { ascending: false }).limit(20);
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("*").order("created_at", { ascending: false }).limit(30);

  return (
    <AppShell section="Contract operations console" subtitle="Admin · GenLayer mirror">
      <div className="space-y-6">
        <div className="panel-violet p-5 relative scanline">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-sage">Source of truth contract</div>
              <div className="font-mono text-pearl break-all mt-1">{AGROSENSE_CONTRACT_ADDRESS}</div>
            </div>
            <ConsensusBadge label={AGROSENSE_CONTRACT_NETWORK} />
          </div>
        </div>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Case queue</div>
            <span className="badge badge-muted">{cases?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>Crop</th><th>Status</th><th>Created</th><th>User</th></tr></thead>
            <tbody>
              {(cases ?? []).map(c => (
                <tr key={c.id}>
                  <td className="font-display text-pearl">{c.crop_type}</td>
                  <td><span className="badge badge-sensor">{c.status}</span></td>
                  <td className="text-sage">{new Date(c.created_at).toLocaleString()}</td>
                  <td className="font-mono text-xs text-sage">{c.user_id.slice(0,8)}…</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <div className="font-display text-pearl text-xl mb-3">Mirrored verdicts</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(verdicts ?? []).map(v => (
              <div key={v.id} className="panel p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-pearl text-lg">{v.verdict}</div>
                  <ConsensusBadge label={v.consensus_status} />
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
                  <div><div className="text-[10px] uppercase text-sage">Risk</div><div className="text-pearl">{v.risk_level}</div></div>
                  <div><div className="text-[10px] uppercase text-sage">Plan</div><div className="text-pearl">{v.selected_plan}</div></div>
                </div>
                <div className="mt-3 flex flex-wrap gap-3"><HashText label="tx" value={v.transaction_hash} /><HashText label="case" value={v.advisory_case_id} /></div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Contract activity stream</div>
            <span className="badge badge-muted">{activity?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>When</th><th>Action</th><th>Status</th><th>Tx</th><th>Error</th></tr></thead>
            <tbody>
              {(activity ?? []).map(a => (
                <tr key={a.id}>
                  <td className="text-sage text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="text-pearl">{a.action}</td>
                  <td><span className={`badge ${a.status === "error" ? "badge-risk" : a.status === "submitted" ? "badge-sensor" : "badge-bio"}`}>{a.status}</span></td>
                  <td><HashText value={a.transaction_hash} /></td>
                  <td className="text-stormclay text-xs max-w-[260px] truncate">{a.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </AppShell>
  );
}
"""

# =========================================================================
#                          PROFILE / WALLET
# =========================================================================

F["app/profile/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";
import { ExportKeyForm } from "./ExportKeyForm";

export default async function ProfilePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: profile } = await sb.from("profiles").select("*").eq("user_id", me.user!.id).maybeSingle();
  const { data: wallet }  = await sb.from("wallets").select("address,created_at").eq("user_id", me.user!.id).maybeSingle();
  const { data: audit }   = await sb.from("recovery_audit_logs").select("*").eq("user_id", me.user!.id).order("created_at",{ascending:false}).limit(10);

  return (
    <AppShell section="Operator profile" subtitle="Identity, embedded wallet, recovery audit">
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7 space-y-5">
          <section className="panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-sage">Email profile</div>
                <div className="font-display text-2xl text-pearl mt-1">{profile?.email}</div>
              </div>
              <span className="badge badge-bio">Active</span>
            </div>
          </section>

          <section className="panel p-6">
            <div className="text-[10px] uppercase tracking-wider text-sage">Embedded wallet</div>
            <div className="font-mono text-pearl mt-2 break-all">{wallet?.address}</div>
            <p className="text-sage text-sm mt-3">
              Your wallet is embedded into your AgroSense profile. It is used to sign GenLayer
              actions in the background. You do not need MetaMask, Rabby, Rainbow, Zerion, or
              any external wallet for normal use.
            </p>
            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              <div><div className="text-[10px] uppercase text-sage">Status</div><div className="text-pearl mt-1">Attached</div></div>
              <div><div className="text-[10px] uppercase text-sage">Created</div><div className="text-pearl mt-1">{wallet?.created_at ? new Date(wallet.created_at).toLocaleDateString() : "—"}</div></div>
            </div>
          </section>

          <ExportKeyForm />
        </div>

        <div className="col-span-12 lg:col-span-5">
          <section className="panel p-6">
            <div className="text-[10px] uppercase tracking-wider text-sage">Recovery audit log</div>
            <ul className="mt-4 space-y-3">
              {(audit ?? []).length === 0 && <li className="text-sage text-sm">No recovery events.</li>}
              {(audit ?? []).map(a => (
                <li key={a.id} className="flex items-start gap-3">
                  <i className={`dot mt-1.5 ${a.action === "privkey_exported" ? "dot-risk" : "dot-bio"}`}></i>
                  <div>
                    <div className="text-pearl text-sm">{a.action}</div>
                    <div className="text-sage text-xs">{new Date(a.created_at).toLocaleString()}</div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
"""

F["app/profile/ExportKeyForm.tsx"] = r""""use client";
import { useState } from "react";
import { exportPrivateKey } from "@/server/actions/auth";

export function ExportKeyForm() {
  const [pk, setPk] = useState<string>();
  const [err, setErr] = useState<string>();
  const [open, setOpen] = useState(false);
  async function action(fd: FormData) {
    setErr(undefined); setPk(undefined);
    const r = await exportPrivateKey(fd);
    if (!r.ok) setErr(r.error); else setPk(r.privateKey);
  }
  return (
    <section className="panel p-6 border border-stormclay/30">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stormclay">Sensitive</div>
          <div className="font-display text-pearl text-xl mt-1">Export private key</div>
        </div>
        <span className="badge badge-risk">Audit logged</span>
      </div>
      <p className="text-sage text-sm mt-2">Anyone with this key controls your embedded wallet. Re-authentication is required and every export is recorded.</p>
      {!open ? (
        <button className="btn-ghost mt-4" onClick={() => setOpen(true)}>I understand — continue</button>
      ) : (
        <form action={action} className="mt-4 space-y-3">
          <input type="password" name="password" required className="input" placeholder="Re-enter password" />
          <button className="btn-violet">Export key</button>
          {err && <p className="text-stormclay text-sm">{err}</p>}
          {pk && <div className="font-mono text-xs p-3 bg-obsidian/70 border border-white/10 rounded-xl break-all">{pk}</div>}
        </form>
      )}
    </section>
  );
}
"""

# =========================================================================
#                              SETTINGS
# =========================================================================

F["app/settings/page.tsx"] = r"""import Link from "next/link";
import { AppShell } from "@/components/AppShell";

export default async function SettingsPage() {
  return (
    <AppShell section="Settings" subtitle="Account · Security · Recovery · Data">
      <div className="grid md:grid-cols-2 gap-5">
        <Panel title="Account"           body="Email profile, display name, role. Email is your primary identity in AgroSense." />
        <Panel title="Security"          body="Password and session management. Use the recovery flow to rotate without resetting the wallet." cta={["Use recovery key","/reset-password"]} />
        <Panel title="Recovery"          body="Your recovery key wraps the embedded wallet. Store it offline. Lost keys cannot be regenerated without rotating the wallet — which is not allowed." />
        <Panel title="Notifications"     body="Email alerts for verdicts, consensus events, and critical risk signals. (Coming soon.)" />
        <Panel title="Data export"       body="Download a full export of your profile, farms, advisory cases, evidence references, and mirrored verdicts. (Coming soon.)" />
        <Panel title="Danger zone" tone="risk" body="Account deletion permanently removes profile and farm records. Wallet ciphertext is destroyed; recovered keys can no longer be derived. (Coming soon.)" />
      </div>
    </AppShell>
  );
}

function Panel({ title, body, cta, tone }: { title: string; body: string; cta?: [string,string]; tone?: "risk" }) {
  return (
    <section className={`panel p-6 ${tone === "risk" ? "border border-stormclay/30" : ""}`}>
      <div className="flex items-center justify-between">
        <div className="font-display text-pearl text-xl">{title}</div>
        {tone === "risk" && <span className="badge badge-risk">Sensitive</span>}
      </div>
      <p className="text-sage text-sm mt-2 leading-relaxed">{body}</p>
      {cta && <Link href={cta[1]} className="btn-ghost mt-4 inline-block">{cta[0]} →</Link>}
    </section>
  );
}
"""

# =========================================================================
#                              DEMO
# =========================================================================

F["app/demo/page.tsx"] = r"""import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { AGROSENSE_CONTRACT_ADDRESS } from "@/lib/genlayer/contract";

const sample = {
  verdict: "Delay planting",
  risk_level: "High rainfall",
  confidence_label: "Strong",
  selected_plan: "B — Delay planting",
  consensus_status: "Validated by GenLayer",
  contract_address: AGROSENSE_CONTRACT_ADDRESS,
  transaction_hash: "0xdemo7f1c8ab0000000000000000000000000000000be02demo",
  advisory_id_on_chain: "demo-1",
  evidence_digest: "soil:9af2b1e7|files:c8ee3d10",
  reasoning_summary:
    "Validators independently reasoned that 7-day rainfall risk combined with incomplete soil confidence makes immediate planting unsafe. Delay is the most defensible action; re-review when soil report completes.",
};

export default function Demo() {
  return (
    <main className="min-h-screen bg-field-grid p-10 space-y-6 max-w-6xl mx-auto">
      <div>
        <span className="badge badge-consensus">Demo verdict · Placeholder data</span>
        <h1 className="font-display text-4xl text-pearl mt-3">Consensus Verdict Terminal</h1>
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7"><VerdictCapsule v={sample} /></div>
        <div className="col-span-12 lg:col-span-5"><GenLayerConsensusPanel v={sample} /></div>
      </div>
    </main>
  );
}
"""

# =========================================================================
def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage4] wrote {n} files")

if __name__ == "__main__":
    main()
