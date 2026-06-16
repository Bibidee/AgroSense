"use client";
import { useState, useTransition } from "react";
import { exportUserData } from "@/server/actions/settings";

export function DataExportButton() {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  function onClick() {
    setErr(undefined);
    start(async () => {
      const r = await exportUserData();
      if (!r.ok) { setErr(r.error || "Export failed"); return; }
      const blob = new Blob([JSON.stringify(r.bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `agrosense-export-${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
  }
  return (
    <div className="mt-3 space-y-2">
      <button type="button" onClick={onClick} disabled={pending}
        className="btn-primary disabled:opacity-60">
        {pending ? "Bundling…" : "Download my data (JSON)"}
      </button>
      {err && <div className="text-stormclay text-sm">{err}</div>}
    </div>
  );
}
