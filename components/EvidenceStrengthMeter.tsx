export function EvidenceStrengthMeter({ score = 60 }: { score?: number }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="panel p-5">
      <div className="text-[10px] uppercase tracking-wider text-sage">Evidence strength</div>
      <div className="font-display text-3xl text-pearl mt-2">{pct}%</div>
      <div className="mt-3 h-2 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "linear-gradient(90deg,#39D98A,#00C2B8)" }} />
      </div>
      <div className="text-xs text-sage mt-2">Soil · Weather · Market · Uploaded files</div>
    </div>
  );
}
