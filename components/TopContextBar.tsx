import Link from "next/link";
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
