import Link from "next/link";
import { txUrl, addressUrl } from "@/lib/genlayer/contract";

export function HashText({
  value, label, kind,
}: { value?: string | null; label?: string; kind?: "tx" | "address" }) {
  if (!value) return <span className="font-mono text-xs text-sage">—</span>;
  const short = value.length > 18 ? `${value.slice(0,8)}…${value.slice(-6)}` : value;
  const href = kind === "tx" ? txUrl(value) : kind === "address" ? addressUrl(value) : null;
  const inner = (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs">
      {label && <span className="text-sage uppercase tracking-wider text-[10px]">{label}</span>}
      <span className={href ? "text-sensor underline-offset-2 hover:underline" : "text-pearl/90"}>{short}</span>
    </span>
  );
  return href ? <Link href={href} target="_blank" rel="noreferrer">{inner}</Link> : inner;
}
