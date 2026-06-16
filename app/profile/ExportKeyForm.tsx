"use client";
import { useState } from "react";
import { exportPrivateKey } from "@/server/actions/auth";

export function ExportKeyForm() {
  const [pk, setPk] = useState<string>();
  const [err, setErr] = useState<string>();
  const [open, setOpen] = useState(false);
  async function action(fd: FormData) {
    setErr(undefined); setPk(undefined);
    const r = await exportPrivateKey(fd);
    if (!r.ok) setErr(r.error); else setPk(r.privateKey);
  }
  return (
    <section className="panel p-6 border border-stormclay/30">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-stormclay">Sensitive</div>
          <div className="font-display text-pearl text-xl mt-1">Export private key</div>
        </div>
        <span className="badge badge-risk">Audit logged</span>
      </div>
      <p className="text-sage text-sm mt-2">Anyone with this key controls your embedded wallet. Re-authentication is required and every export is recorded.</p>
      {!open ? (
        <button className="btn-ghost mt-4" onClick={() => setOpen(true)}>I understand — continue</button>
      ) : (
        <form action={action} className="mt-4 space-y-3">
          <input type="password" name="password" required className="input" placeholder="Re-enter password" />
          <button className="btn-violet">Export key</button>
          {err && <p className="text-stormclay text-sm">{err}</p>}
          {pk && <div className="font-mono text-xs p-3 bg-obsidian/70 border border-white/10 rounded-xl break-all">{pk}</div>}
        </form>
      )}
    </section>
  );
}
