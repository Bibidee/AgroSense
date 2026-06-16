"use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { submitToGenLayer } from "@/server/actions/cases";
import { txUrl } from "@/lib/genlayer/contract";

export function SubmitButton({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  const [okTx, setOkTx] = useState<string>();
  const [showPw, setShowPw] = useState(false);
  const [password, setPassword] = useState("");
  const router = useRouter();

  function onClick() {
    setErr(undefined); setOkTx(undefined);
    setShowPw(true);
  }

  function onConfirm() {
    if (!password) { setErr("Enter your password to sign with your embedded wallet."); return; }
    setErr(undefined);
    console.log("[AgroSense] Submit to GenLayer clicked, caseId =", caseId);
    start(async () => {
      try {
        const r = await submitToGenLayer(caseId, password);
        console.log("[AgroSense] Submit result:", r);
        setPassword("");
        setShowPw(false);
        if (!(r as any)?.ok) {
          setErr((r as any)?.error || "Submission failed");
          return;
        }
        setOkTx((r as any).txHash);
        router.refresh();
      } catch (e) {
        console.error("[AgroSense] Submit threw:", e);
        setErr(e instanceof Error ? e.message : "Submission failed");
      }
    });
  }

  return (
    <div className="mt-4 space-y-3">
      {!showPw && (
        <button type="button" onClick={onClick} disabled={pending}
          className="btn-violet w-full disabled:opacity-60 disabled:cursor-not-allowed">
          Submit to GenLayer →
        </button>
      )}

      {showPw && (
        <div className="rounded-xl border border-consensus/40 bg-obsidian/70 p-3 space-y-2">
          <div className="text-[10px] uppercase tracking-wider text-sage">Sign with embedded wallet</div>
          <p className="text-xs text-pearl/70">
            Your wallet stays on the server only to sign this single transaction.
            Confirm with your password.
          </p>
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") onConfirm(); }}
            placeholder="Password"
            className="input"
            disabled={pending}
          />
          <div className="flex gap-2">
            <button type="button" onClick={onConfirm} disabled={pending}
              className="btn-violet flex-1 disabled:opacity-60">
              {pending ? "Signing & submitting…" : "Sign & submit"}
            </button>
            <button type="button" disabled={pending}
              onClick={() => { setShowPw(false); setPassword(""); setErr(undefined); }}
              className="btn-ghost">Cancel</button>
          </div>
        </div>
      )}

      {okTx && (
        <div className="rounded-xl border border-biosignal/40 bg-biosignal/10 p-3 text-sm text-pearl">
          <div className="font-display text-biosignal">Submitted from your wallet</div>
          <a href={txUrl(okTx)!} target="_blank" rel="noreferrer" className="font-mono text-xs text-sensor underline-offset-2 hover:underline break-all">
            View tx on explorer · {okTx.slice(0,10)}…{okTx.slice(-6)}
          </a>
        </div>
      )}
      {err && (
        <div className="rounded-xl border border-stormclay/40 bg-stormclay/10 p-3 text-sm text-pearl">
          <div className="font-display text-stormclay">Submit failed</div>
          <div className="mt-1 text-pearl/80 break-words">{err}</div>
        </div>
      )}
    </div>
  );
}
