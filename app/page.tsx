import Link from "next/link";
import { Brand } from "@/components/Brand";
import { ConsensusBadge, LiveBadge, RiskBadge, ActionWindowBadge } from "@/components/Badges";
import { AGROSENSE_CONTRACT_ADDRESS, AGROSENSE_CONTRACT_NETWORK } from "@/lib/genlayer/contract";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-field-grid">
      <nav className="max-w-7xl mx-auto flex items-center justify-between px-6 py-5">
        <Brand />
        <div className="flex items-center gap-3">
          <LiveBadge label="StudioNet · Live" />
          <Link href="/login" className="btn-ghost text-sm">Log in</Link>
          <Link href="/signup" className="btn-primary text-sm">Create account</Link>
        </div>
      </nav>

      {/* HERO */}
      <section className="max-w-7xl mx-auto px-6 pt-10 pb-20 grid lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7">
          <span className="badge badge-consensus">GenLayer · Field Intelligence OS</span>
          <h1 className="font-display text-5xl md:text-7xl font-bold text-pearl mt-5 leading-[1.05] tracking-tight">
            The farm decision layer<br/>
            powered by <span className="text-biosignal">consensus</span>.
          </h1>
          <p className="mt-6 text-lg text-sage max-w-xl leading-relaxed">
            Turn uncertain planting, irrigation, harvest, and risk decisions into GenLayer
            consensus-backed advisory verdicts. AgroSense prepares the case — independent
            validators issue the verdict.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/signup" className="btn-primary">+ Create advisory case</Link>
            <Link href="/demo"   className="btn-ghost">View demo verdict →</Link>
          </div>
          <div className="mt-10 flex items-center gap-6 text-xs text-sage">
            <span className="flex items-center gap-2"><i className="dot dot-bio"></i>Embedded wallet</span>
            <span className="flex items-center gap-2"><i className="dot dot-sensor"></i>Live data</span>
            <span className="flex items-center gap-2"><i className="dot dot-violet"></i>Validator consensus</span>
          </div>
        </div>

        {/* Hero terminal */}
        <div className="lg:col-span-5">
          <div className="panel-violet p-6 relative scanline">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-sage">ADVISORY · KADUNA-NORTH-001</span>
              <ConsensusBadge />
            </div>
            <div className="mt-4">
              <div className="text-[10px] uppercase tracking-wider text-sage">Verdict</div>
              <div className="font-display text-4xl text-pearl font-bold">Delay planting</div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-5">
              <Field k="Crop" v="Maize" />
              <Field k="Region" v="Kaduna North" />
              <Field k="Weather" v="Mixed rainfall" tone="sensor" />
              <Field k="Soil report" v="Incomplete" tone="gold" />
              <Field k="Market" v="Positive" tone="bio" />
              <Field k="GenLayer" v="Consensus reached" tone="violet" />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <RiskBadge level="High rainfall" />
              <ActionWindowBadge window="Review in 5 days" />
            </div>
            <div className="mt-5 pt-4 border-t border-white/10 text-[11px] font-mono text-sage break-all">
              {AGROSENSE_CONTRACT_NETWORK} · {AGROSENSE_CONTRACT_ADDRESS}
            </div>
          </div>
        </div>
      </section>

      {/* Why not ordinary AI */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-[11px] uppercase tracking-[0.2em] text-sage">Why this is not ordinary AI advice</div>
        <h2 className="font-display text-4xl text-pearl mt-3">One question. Three approaches.</h2>
        <div className="grid md:grid-cols-3 gap-5 mt-8">
          <Compare
            tag="Normal AI tool" tagTone="muted"
            title="One private recommendation"
            body="A single black-box model gives one answer. No second opinion. No proof of reasoning. No way to know if a different model would disagree."
          />
          <Compare
            tag="Threshold app" tagTone="gold"
            title="Fixed weather rules"
            body="If rainfall > X, plant. Predictable, brittle, blind to context. Cannot weigh competing signals like market, soil, and observation together."
          />
          <Compare
            tag="AgroSense" tagTone="violet" highlight
            title="Validator consensus"
            body="The advisory packet is submitted to a GenLayer Intelligent Contract. Independent validators reason over the evidence and converge on the most defensible action."
          />
        </div>
      </section>

      {/* Capabilities */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-4 gap-4">
          {[
            ["Embedded wallet", "Auto-created at signup. Permanent. Used silently for GenLayer signing."],
            ["Evidence vault",  "Soil PDFs, farm imagery, market screenshots — hashed and submitted by reference."],
            ["Consensus verdict", "Validators issue the verdict. AgroSense never decides."],
            ["Audit trail",     "Every advisory case mirrors its on-chain result, hash, and transaction."],
          ].map(([t, d]) => (
            <div key={t} className="panel p-5">
              <div className="text-pearl font-display text-lg">{t}</div>
              <div className="text-sage text-sm mt-2 leading-relaxed">{d}</div>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/5 mt-10">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-wrap justify-between gap-3 text-xs text-sage">
          <span>© AgroSense — Field Intelligence OS</span>
          <span className="font-mono">{AGROSENSE_CONTRACT_NETWORK} · {AGROSENSE_CONTRACT_ADDRESS}</span>
        </div>
      </footer>
    </main>
  );
}

function Field({ k, v, tone }: { k: string; v: string; tone?: "bio"|"sensor"|"gold"|"violet" }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-sage">{k}</div>
      <div className="text-pearl font-display flex items-center gap-2 mt-1">
        {tone && <i className={`dot dot-${tone}`}></i>}{v}
      </div>
    </div>
  );
}

function Compare({ tag, tagTone, title, body, highlight }: { tag: string; tagTone: "muted"|"gold"|"violet"; title: string; body: string; highlight?: boolean }) {
  return (
    <div className={`panel p-6 ${highlight ? "ring-1 ring-consensus/40 shadow-violet" : ""}`}>
      <span className={`badge badge-${tagTone === "muted" ? "muted" : tagTone === "gold" ? "gold" : "consensus"}`}>{tag}</span>
      <div className="font-display text-pearl text-xl mt-3">{title}</div>
      <p className="text-sage text-sm mt-3 leading-relaxed">{body}</p>
    </div>
  );
}
