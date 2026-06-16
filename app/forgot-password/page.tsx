import Link from "next/link";
import { Brand } from "@/components/Brand";

export default function P() {
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
          <span className="badge badge-gold">Recovery</span>
          <h1 className="font-display text-4xl text-pearl mt-3">Lost password?</h1>
          <p className="text-sage mt-3">Use your recovery key to set a new password. Your embedded wallet stays the same — only the password wrap is replaced.</p>
          <Link href="/reset-password" className="btn-primary inline-block mt-6">Use recovery key →</Link>
        </div>
      </section>
    </main>
  );
}
