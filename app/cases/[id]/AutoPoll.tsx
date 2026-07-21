"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { refreshVerdict } from "@/server/actions/cases";

const MAX_CHECKS = 40; // ~5 min at 8s intervals

export function AutoPoll({ caseId, enabled }: { caseId: string; enabled: boolean }) {
  const [msg, setMsg] = useState<string>();
  const [timedOut, setTimedOut] = useState(false);
  const ticks = useRef(0);
  const router = useRouter();

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    async function tick() {
      if (cancelled) return;
      ticks.current += 1;

      if (ticks.current > MAX_CHECKS) {
        setTimedOut(true);
        return;
      }

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

  if (timedOut) {
    return (
      <div className="mt-3 space-y-2">
        <div className="text-xs text-amber-400 font-medium">Consensus undetermined</div>
        <p className="text-[11px] text-sage leading-relaxed">
          Validators could not reach agreement on this case after {MAX_CHECKS} checks.
          This usually means the evidence was insufficient for a clear verdict.
          Add more evidence and resubmit, or check the{" "}
          <a
            href={`https://explorer-studio.genlayer.com`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-violet-400 underline"
          >
            GenLayer explorer
          </a>{" "}
          for details.
        </p>
      </div>
    );
  }

  return <div className="text-[10px] text-sage mt-2">{msg ?? "Polling on-chain…"}</div>;
}
