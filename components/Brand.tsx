export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "h-10 w-10" : size === "sm" ? "h-7 w-7" : "h-9 w-9";
  const font = size === "lg" ? "text-2xl" : size === "sm" ? "text-base" : "text-lg";
  return (
    <div className="flex items-center gap-2.5">
      <div className={`${dim} rounded-xl relative overflow-hidden`}
        style={{ background: "linear-gradient(135deg,#39D98A,#00C2B8 60%,#8B5CF6)" }}>
        <div className="absolute inset-[3px] rounded-[10px] bg-obsidian grid place-items-center text-biosignal font-display font-bold">A</div>
      </div>
      <div className="leading-none">
        <div className={`font-display font-bold text-pearl ${font}`}>AgroSense</div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-sage mt-1">Field Intelligence OS</div>
      </div>
    </div>
  );
}
