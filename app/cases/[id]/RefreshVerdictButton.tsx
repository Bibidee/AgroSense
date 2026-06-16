"use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { refreshVerdict } from "@/server/actions/cases";

export function RefreshVerdictButton({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();
  const router = useRouter();
  return (
    <>
      <button type="button" disabled={pending}
        onClick={() => {
          setMsg(undefined);
          start(async () => {
            try {
              const r = await refreshVerdict(caseId);
              if (!r.ok) setMsg(r.error || "No verdict yet on-chain.");
              else { setMsg("Verdict synced."); router.refresh(); }
            } catch (e) { setMsg(e instanceof Error ? e.message : "Refresh failed"); }
          });
        }}
        className="btn-ghost w-full disabled:opacity-60">
        {pending ? "Checking on-chain…" : "Refresh verdict"}
      </button>
      {msg && <div className="text-xs text-sage">{msg}</div>}
    </>
  );
}
