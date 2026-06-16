"use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { replayCase, exportAdvisoryPacket } from "@/server/actions/admin";

export function AdminCaseActions({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();
  const router = useRouter();
  function doReplay() {
    setMsg(undefined);
    if (!confirm("Replay this case? The mirrored verdict will be cleared.")) return;
    start(async () => {
      const r: any = await replayCase(caseId);
      if (!r.ok) { setMsg(r.error || "Replay failed"); return; }
      setMsg("Replay queued."); router.refresh();
    });
  }
  function doExport() {
    setMsg(undefined);
    start(async () => {
      const r: any = await exportAdvisoryPacket(caseId);
      if (!r.ok) { setMsg(r.error || "Export failed"); return; }
      const blob = new Blob([JSON.stringify(r.bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url;
      a.download = `advisory-packet-${caseId}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
  }
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <button onClick={doReplay}  disabled={pending} className="btn-ghost text-xs disabled:opacity-50">Replay</button>
      <button onClick={doExport}  disabled={pending} className="btn-ghost text-xs disabled:opacity-50">Export packet</button>
      {msg && <span className="text-sage">{msg}</span>}
    </div>
  );
}
