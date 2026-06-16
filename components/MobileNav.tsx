"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/dashboard", label: "Home",     glyph: "◎" },
  { href: "/cases/new", label: "New",      glyph: "+" },
  { href: "/cases",     label: "Cases",    glyph: "≡" },
  { href: "/evidence",  label: "Evidence", glyph: "▣" },
  { href: "/profile",   label: "Profile",  glyph: "◐" },
];

export function MobileNav() {
  const path = usePathname() ?? "";
  const activeHref = ITEMS
    .filter(n => path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href + "/")))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-graphite/95 backdrop-blur border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
      <div className="grid grid-cols-5">
        {ITEMS.map(n => {
          const on = activeHref === n.href;
          return (
            <Link key={n.href} href={n.href}
              className={`flex flex-col items-center justify-center py-2.5 text-[10px] uppercase tracking-wider ${on ? "text-biosignal" : "text-sage"}`}>
              <span className={`w-8 h-8 grid place-items-center rounded-lg mb-0.5 ${on ? "bg-biosignal/15 border border-biosignal/30" : "bg-white/5 border border-transparent"}`}>{n.glyph}</span>
              {n.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
