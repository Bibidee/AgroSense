import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { AGROSENSE_CONTRACT_ADDRESS } from "@/lib/genlayer/contract";

const sample = {
  verdict: "Delay planting",
  risk_level: "High rainfall",
  confidence_label: "Strong",
  selected_plan: "B — Delay planting",
  consensus_status: "Validated by GenLayer",
  contract_address: AGROSENSE_CONTRACT_ADDRESS,
  transaction_hash: "0xdemo7f1c8ab0000000000000000000000000000000be02",
  advisory_id_on_chain: "demo-1",
  evidence_digest: "soil:9af2b1e7|files:c8ee3d10",
  reasoning_summary:
    "Validators independently reasoned that 7-day rainfall risk combined with incomplete soil confidence makes immediate planting unsafe. Delay is the most defensible action.",
};

export default function Demo() {
  return (
    <main className="min-h-screen bg-field-grid p-10 space-y-6 max-w-6xl mx-auto">
      <div>
        <span className="badge badge-consensus">Demo · Placeholder data (not on-chain)</span>
        <h1 className="font-display text-4xl text-pearl mt-3">Consensus Verdict Terminal</h1>
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7"><VerdictCapsule v={sample} status="consensus_reached" /></div>
        <div className="col-span-12 lg:col-span-5"><GenLayerConsensusPanel v={sample} status="consensus_reached" /></div>
      </div>
    </main>
  );
}
