import { HashText } from "./HashText";

export function ContractActivityStream({ items }: { items: any[] }) {
  if (!items?.length)
    return <div className="panel p-5 text-sage text-sm">No contract activity yet. Submitting a case will log GenLayer interaction here.</div>;
  return (
    <div className="panel p-5">
      <div className="text-[10px] uppercase tracking-wider text-sage">Contract activity stream</div>
      <ul className="mt-3 space-y-3">
        {items.map((a, i) => (
          <li key={i} className="flex items-start gap-3">
            <i className={`dot mt-1.5 ${a.status === "error" ? "dot-risk" : a.status === "submitted" ? "dot-sensor" : "dot-bio"}`}></i>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-pearl">{a.action} · <span className="text-sage">{a.status}</span></div>
              <div className="text-xs text-sage mt-1 flex flex-wrap gap-3">
                <HashText label="tx" value={a.transaction_hash} kind="tx" />
                <span>{new Date(a.created_at).toLocaleString()}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
