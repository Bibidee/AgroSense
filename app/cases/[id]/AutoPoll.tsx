"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { refreshVerdict } from "@/server/actions/cases";

// Polls the contract every 8s while the case is in awaiting_consensus.
// Calls router.refresh() when the verdict lands so the SSR-rendered
// VerdictCapsule + ConsensusPanel hydrate with the real result.
export function AutoPoll({ caseId, enabled }: { caseId: string; enabled: boolean }) {
  const [msg, setMsg] = useState<string>();
  const ticks = useRef(0);
  const router = useRouter();

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    async function tick() {
      if (cancelled) return;
      ticks.current += 1;
      try {
        const r = await refreshVerdict(caseId);
        if (cancelled) return;
        if (r.ok) { setMsg("Verdict synced. Refreshing…"); router.refresh(); return; }
        setMsg(`Awaiting validators · checked ${ticks.current}×`);
      } catch (e) {
        if (!cancelled) setMsg(e instanceof Error ? e.message : "Poll error");
      }
    }
    tick();
    const id = setInterval(tick, 8000);
    return () => { cancelled = true; clearInterval(id); };
  }, [caseId, enabled, router]);

  if (!enabled) return null;
  return <div className="text-[10px] text-sage mt-2">{msg ?? "Polling on-chain…"}</div>;
}
