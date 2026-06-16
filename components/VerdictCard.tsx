export function VerdictCard({ v }: { v: {
  verdict: string; risk_level: string; confidence_label: string;
  selected_plan: string; consensus_status: string;
  contract_address: string; transaction_hash: string;
  evidence_digest: string; reasoning_summary?: string | null;
}}) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-olive">{v.contract_address?.slice(0,10)}…</span>
        <span className="badge-consensus">{v.consensus_status}</span>
      </div>
      <div className="mt-4">
        <div className="text-xs uppercase tracking-wider text-olive">Verdict</div>
        <div className="font-display text-3xl text-canopy font-bold">{v.verdict}</div>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-5">
        <div><div className="text-xs text-olive uppercase">Risk</div><div className="mt-1"><span className="badge-risk">{v.risk_level}</span></div></div>
        <div><div className="text-xs text-olive uppercase">Confidence</div><div className="mt-1"><span className="badge-ok">{v.confidence_label}</span></div></div>
        <div><div className="text-xs text-olive uppercase">Selected plan</div><div className="mt-1 font-display text-canopy">{v.selected_plan}</div></div>
        <div><div className="text-xs text-olive uppercase">Evidence digest</div><div className="mt-1 font-mono text-xs text-olive truncate">{v.evidence_digest}</div></div>
      </div>
      {v.reasoning_summary && (
        <div className="mt-5">
          <div className="text-xs text-olive uppercase">Why this verdict</div>
          <p className="mt-1 text-sm text-charcoal leading-relaxed">{v.reasoning_summary}</p>
        </div>
      )}
      <div className="mt-5 pt-4 border-t border-sage text-xs font-mono text-olive break-all">
        tx {v.transaction_hash}
      </div>
    </div>
  );
}
