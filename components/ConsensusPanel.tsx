export function ConsensusPanel({ v }: { v: any }) {
  return (
    <div className="rounded-2xl p-6 text-ivory" style={{ background: "#0B3D2E" }}>
      <div className="flex items-center justify-between">
        <span className="font-display text-lg">GenLayer Consensus</span>
        <span className="badge-consensus">{v.consensus_status}</span>
      </div>
      <dl className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div><dt className="text-sage uppercase text-xs">Contract</dt><dd className="font-mono break-all">{v.contract_address}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Advisory ID</dt><dd className="font-mono break-all">{v.advisory_id_on_chain}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Tx hash</dt><dd className="font-mono break-all">{v.transaction_hash}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Source of truth</dt><dd>GenLayer Intelligent Contract</dd></div>
      </dl>
    </div>
  );
}
