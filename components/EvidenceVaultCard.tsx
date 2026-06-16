import { HashText } from "./HashText";

export function EvidenceVaultCard({ f }: { f: any }) {
  const type = (f.file_type || "").split("/").pop()?.toUpperCase();
  return (
    <div className="panel p-5 lift">
      <div className="flex items-center justify-between">
        <span className="badge badge-muted">{type ?? "FILE"}</span>
        <span className="badge badge-bio">In vault</span>
      </div>
      <div className="font-mono text-xs mt-3 break-all text-pearl/80">{f.file_path}</div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
        <div><div className="text-[10px] uppercase text-sage">Size</div><div className="text-pearl">{(f.file_size/1024).toFixed(1)} KB</div></div>
        <div><div className="text-[10px] uppercase text-sage">Uploaded</div><div className="text-pearl">{new Date(f.created_at).toLocaleDateString()}</div></div>
      </div>
      <div className="mt-3"><HashText label="sha256" value={f.evidence_hash} /></div>
    </div>
  );
}
