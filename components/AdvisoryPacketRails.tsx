import { HashText } from "./HashText";
import { ConsensusBadge } from "./Badges";

export function LeftPacketRail({ farms, c }: { farms: any[]; c?: any }) {
  return (
    <aside className="panel p-5 sticky top-24">
      <div className="text-[10px] uppercase tracking-wider text-sage">Advisory packet</div>
      <div className="mt-4 space-y-3 text-sm">
        <Row k="Farms available" v={`${farms.length}`} />
        <Row k="Crop" v={c?.crop_type ?? "—"} />
        <Row k="Decision" v={c?.decision_type ?? "—"} />
        <Row k="Status" v={c?.status ?? "draft"} />
      </div>
      <div className="hr my-4" />
      <div className="text-[10px] uppercase tracking-wider text-sage">Readiness</div>
      <div className="mt-2 h-2 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full" style={{ width: c ? "70%" : "30%", background: "linear-gradient(90deg,#39D98A,#00C2B8)" }} />
      </div>
    </aside>
  );
}

export function RightPacketRail({ verdict }: { verdict?: any }) {
  return (
    <aside className="panel-violet p-5 sticky top-24 relative scanline">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer readiness</div>
        <ConsensusBadge label="Awaiting submission" />
      </div>
      <p className="text-sm text-pearl/80 mt-3">
        AgroSense prepares the advisory packet. The final verdict is produced by independent
        GenLayer validators reaching consensus on the most defensible action.
      </p>
      <div className="hr my-4" />
      <div className="text-[10px] uppercase tracking-wider text-sage">Mirrored verdict</div>
      <div className="mt-2 text-sm text-pearl">{verdict?.verdict ?? "Not yet issued"}</div>
      {verdict && <div className="mt-2"><HashText label="tx" value={verdict.transaction_hash} /></div>}
    </aside>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sage text-xs uppercase tracking-wider">{k}</span>
      <span className="text-pearl text-sm font-display truncate max-w-[55%] text-right">{v}</span>
    </div>
  );
}
