"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./Brand";
import { ConsensusBadge } from "./Badges";
import { AGROSENSE_CONTRACT_ADDRESS } from "@/lib/genlayer/contract";

const NAV = [
  { href: "/dashboard", label: "Dashboard", glyph: "◎" },
  { href: "/farms",     label: "Farms",     glyph: "▦" },
  { href: "/cases/new", label: "New case",  glyph: "+" },
  { href: "/cases",     label: "Cases",     glyph: "≡" },
  { href: "/evidence",  label: "Evidence",  glyph: "▣" },
  { href: "/profile",   label: "Profile",   glyph: "◐" },
  { href: "/settings",  label: "Settings",  glyph: "⚙" },
];

export function CommandRail({ admin, email, wallet }: { admin?: boolean; email?: string | null; wallet?: string | null }) {
  const path = usePathname() ?? "";
  // Pick the single longest-prefix match so /cases/new doesn't also light /cases.
  const activeHref = NAV
    .filter(n => path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href + "/")))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;
  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-white/5 bg-graphite/60 backdrop-blur-md">
      <div className="px-5 pt-5 pb-4"><Brand /></div>
      <div className="px-3 pt-2 pb-3"><div className="hr" /></div>
      <nav className="flex-1 px-3 space-y-1">
        {NAV.map(n => {
          const on = activeHref === n.href;
          return (
            <Link key={n.href} href={n.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition
                ${on ? "bg-biosignal/10 text-biosignal border border-biosignal/30 shadow-glow"
                     : "text-pearl/80 hover:text-pearl hover:bg-white/5 border border-transparent"}`}>
              <span className={`w-6 h-6 grid place-items-center rounded-md text-xs ${on ? "bg-biosignal/20" : "bg-white/5"}`}>{n.glyph}</span>
              <span>{n.label}</span>
              {on && <span className="ml-auto dot dot-bio"></span>}
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
          <div className="font-mono text-[10px] text-sage mt-2 break-all">{AGROSENSE_CONTRACT_ADDRESS.slice(0,10)}…{AGROSENSE_CONTRACT_ADDRESS.slice(-6)}</div>
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
