"use client";
import { useEffect, useState } from "react";
import { VerdictCapsule } from "./VerdictCapsule";

// Cycles through past verdicts with a soft cross-fade.
// Shows nothing if there are zero verdicts, the single capsule if one,
// auto-advances every `intervalMs` if two or more.
export function VerdictRotator({
  verdicts, intervalMs = 7000,
}: { verdicts: any[]; intervalMs?: number }) {
  const [i, setI] = useState(0);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (verdicts.length < 2) return;
    const id = setInterval(() => {
      setFading(true);
      setTimeout(() => {
        setI(prev => (prev + 1) % verdicts.length);
        setFading(false);
      }, 280);
    }, intervalMs);
    return () => clearInterval(id);
  }, [verdicts.length, intervalMs]);

  if (verdicts.length === 0) {
    return <VerdictCapsule status="not_submitted" />;
  }
  const v = verdicts[i];

  function jumpTo(idx: number) {
    if (idx === i) return;
    setFading(true);
    setTimeout(() => { setI(idx); setFading(false); }, 200);
  }

  return (
    <div className="relative">
      <div
        className="transition-opacity duration-300"
        style={{ opacity: fading ? 0 : 1 }}
      >
        <VerdictCapsule v={v} status="consensus_reached" />
      </div>

      {verdicts.length > 1 && (
        <div className="absolute top-3 right-3 flex items-center gap-2 z-10">
          <span className="badge badge-muted !py-0 !px-2 !text-[10px]">
            {i + 1} / {verdicts.length}
          </span>
          <div className="flex gap-1">
            {verdicts.map((_, idx) => (
              <button
                key={idx}
                aria-label={`Show verdict ${idx + 1}`}
                onClick={() => jumpTo(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  idx === i ? "w-6 bg-consensus" : "w-1.5 bg-white/20 hover:bg-white/40"
                }`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
