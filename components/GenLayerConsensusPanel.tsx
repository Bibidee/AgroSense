import { ConsensusBadge, SourceOfTruthBadge } from "./Badges";
import { HashText } from "./HashText";

type Status = "not_submitted" | "awaiting_consensus" | "consensus_reached";

export function GenLayerConsensusPanel({
  v, status = "not_submitted", txHash,
}: { v?: any; status?: Status; txHash?: string | null }) {
  const label =
    status === "consensus_reached" ? "Consensus reached"
    : status === "awaiting_consensus" ? "Awaiting consensus"
    : "Not submitted";
  return (
    <div className="panel p-6 relative scanline">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer Adjudication</div>
          <div className="font-display text-pearl text-xl mt-1">Consensus module</div>
        </div>
        <SourceOfTruthBadge />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-5 text-sm">
        <div><div className="text-[10px] uppercase text-sage">Network</div><div className="text-pearl">StudioNet</div></div>
        <div><div className="text-[10px] uppercase text-sage">Status</div><div><ConsensusBadge label={label} /></div></div>
        <div><div className="text-[10px] uppercase text-sage">Contract</div><HashText value={v?.contract_address} kind="address" /></div>
        <div><div className="text-[10px] uppercase text-sage">Advisory ID</div><HashText value={v?.advisory_id_on_chain} /></div>
        <div className="col-span-2"><div className="text-[10px] uppercase text-sage">Transaction</div><HashText value={v?.transaction_hash ?? txHash} kind="tx" /></div>
      </div>
    </div>
  );
}
