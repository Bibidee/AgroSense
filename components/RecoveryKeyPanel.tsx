"use client";
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
