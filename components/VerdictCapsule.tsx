import { ConsensusBadge, RiskBadge, ActionWindowBadge } from "./Badges";
import { HashText } from "./HashText";

type Status = "not_submitted" | "awaiting_consensus" | "consensus_reached";

export function VerdictCapsule({
  v, status = "not_submitted", txHash,
}: { v?: any; status?: Status; txHash?: string | null }) {
  if (status === "not_submitted" || (!v && status === "consensus_reached")) {
    return (
      <div className="panel p-6 relative scanline">
        <div className="text-[10px] uppercase tracking-wider text-sage">Latest verdict</div>
        <div className="font-display text-2xl text-pearl/60 mt-2">Not submitted</div>
        <div className="text-sage text-sm mt-1">Submit the advisory packet to GenLayer to request a consensus verdict.</div>
      </div>
    );
  }
  if (status === "awaiting_consensus" || !v) {
    return (
      <div className="panel p-6 relative scanline">
        <div className="flex items-center justify-between">
          <div className="text-[10px] uppercase tracking-wider text-sage">Consensus verdict</div>
          <span className="badge badge-sensor"><i className="dot dot-sensor pulse-consensus"></i>Awaiting consensus</span>
        </div>
        <div className="font-display text-3xl text-pearl mt-3">Validators reasoning…</div>
        <p className="text-sage text-sm mt-2">Transaction submitted. Verdict will appear here when validators converge on-chain.</p>
        {txHash && (
          <div className="mt-4 pt-3 border-t border-white/10">
            <HashText label="tx" value={txHash} kind="tx" />
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="panel-violet p-6 relative scanline lift">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Consensus verdict</div>
        <ConsensusBadge label={v.consensus_status ?? "Validated"} />
      </div>
      <div className="font-display text-4xl text-pearl mt-3">{v.verdict}</div>
      <div className="flex flex-wrap gap-2 mt-3">
        {v.risk_level && <RiskBadge level={v.risk_level} />}
        {v.confidence_label && <span className="badge badge-bio">{v.confidence_label} confidence</span>}
        <ActionWindowBadge window="Review window 5d" />
      </div>
      {v.reasoning_summary && (
        <p className="text-sm text-pearl/80 mt-4 leading-relaxed">{v.reasoning_summary}</p>
      )}
      <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-4">
        <HashText label="tx" value={v.transaction_hash} kind="tx" />
        <HashText label="contract" value={v.contract_address} kind="address" />
        <HashText label="digest" value={v.evidence_digest} />
      </div>
    </div>
  );
}
