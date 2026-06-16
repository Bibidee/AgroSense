import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { EvidenceVaultCard } from "@/components/EvidenceVaultCard";

export default async function EvidenceRoom() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: ev } = await sb.from("evidence_files")
    .select("*").eq("user_id", me.user!.id).order("created_at", { ascending: false });

  return (
    <AppShell section="Evidence vault" subtitle="Hashed soil reports, imagery, snapshots">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-pearl">All evidence</h1>
          <p className="text-sage text-sm mt-1">Each item is hashed and referenced by digest in the GenLayer advisory packet.</p>
        </div>
        <span className="badge badge-muted">{ev?.length ?? 0} items</span>
      </div>

      {(ev ?? []).length === 0 ? (
        <div className="panel p-10 text-center text-sage mt-6">No evidence yet. Upload from a case to populate the vault.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
          {ev!.map(f => <EvidenceVaultCard key={f.id} f={f} />)}
        </div>
      )}
    </AppShell>
  );
}
