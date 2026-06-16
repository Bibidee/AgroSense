export function CropWindowTimeline() {
  const days = Array.from({ length: 14 }, (_, i) => i + 1);
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Crop window — 14 days</div>
        <span className="badge badge-gold">Caution window</span>
      </div>
      <div className="mt-3 grid grid-cols-14 gap-1">
        {days.map(d => {
          const tone =
            d <= 4 ? "bg-stormclay/60"
            : d <= 7 ? "bg-yieldgold/60"
            : "bg-biosignal/60";
          return (
            <div key={d} className="flex flex-col items-center gap-1">
              <div className={`w-full h-10 rounded-md ${tone}`}></div>
              <div className="text-[10px] text-sage">{d}</div>
            </div>
          );
        })}
      </div>
      <style>{`.grid-cols-14{grid-template-columns:repeat(14,minmax(0,1fr));}`}</style>
    </div>
  );
}
