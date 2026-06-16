"use client";
import { useState } from "react";
import Link from "next/link";
import { signUp } from "@/server/actions/auth";
import { RecoveryKeyPanel } from "@/components/RecoveryKeyPanel";
import { Brand } from "@/components/Brand";

export default function SignupPage() {
  const [err, setErr] = useState<string>();
  const [recoveryKey, setRecoveryKey] = useState<string>();

  async function action(fd: FormData) {
    const r = await signUp(fd);
    if (!r.ok) setErr(r.error); else setRecoveryKey(r.recoveryKey);
  }

  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-field-grid">
      <aside className="hidden md:flex flex-col justify-between p-10 bg-graphite/60 border-r border-white/5 relative overflow-hidden">
        <div className="relative z-10"><Brand size="lg" /></div>
        <div className="relative z-10 max-w-md">
          <span className="badge badge-consensus">Field Intelligence OS</span>
          <h2 className="font-display text-4xl text-pearl mt-4 leading-tight">Consensus-backed farm decisions begin at the access terminal.</h2>
          <p className="text-sage mt-4 leading-relaxed">
            Your AgroSense profile includes a secure embedded wallet used only for GenLayer
            actions. You do not need MetaMask, Rabby, Rainbow, or Zerion for normal use.
          </p>
        </div>
        <div className="relative z-10 flex gap-3">
          <span className="badge badge-bio"><i className="dot dot-bio"></i>Embedded wallet</span>
          <span className="badge badge-sensor"><i className="dot dot-sensor"></i>Live signals</span>
          <span className="badge badge-consensus"><i className="dot dot-violet"></i>Validator consensus</span>
        </div>
        <div className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full opacity-30"
          style={{ background: "radial-gradient(circle, rgba(57,217,138,0.35), transparent 60%)" }} />
        <div className="absolute -top-32 -left-20 w-80 h-80 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.35), transparent 60%)" }} />
      </aside>
      <section className="flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {!recoveryKey ? (
            <>
              <span className="badge badge-bio">Access terminal · Signup</span>
              <h1 className="font-display text-4xl text-pearl mt-3">Create your operator profile</h1>
              <p className="text-sage text-sm mt-2">A secure embedded wallet is created automatically and linked to your profile.</p>
              <form action={action} className="panel p-6 mt-6 space-y-3">
                <label className="text-[10px] uppercase tracking-wider text-sage">Email</label>
                <input name="email" type="email" required className="input" placeholder="operator@farm.org" />
                <label className="text-[10px] uppercase tracking-wider text-sage">Password</label>
                <input name="password" type="password" required minLength={8} className="input" placeholder="Minimum 8 characters" />
                <button className="btn-primary w-full mt-2" type="submit">Initialise profile</button>
                {err && <p className="text-stormclay text-sm mt-1">{err}</p>}
              </form>
              <p className="text-sm text-sage mt-4">Already have an account? <Link href="/login" className="text-biosignal">Log in</Link></p>
            </>
          ) : (
            <>
              <span className="badge badge-consensus">Operator initialised</span>
              <h1 className="font-display text-4xl text-pearl mt-3">Wallet attached</h1>
              <RecoveryKeyPanel recoveryKey={recoveryKey} />
              <Link href="/login" className="btn-primary mt-6 inline-block">Continue to access terminal</Link>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
