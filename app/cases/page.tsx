import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";

export default async function CasesListPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: cases } = await sb.from("advisory_cases")
    .select("id,crop_type,status,decision_type,advisory_question,created_at,farms(name,country,region)")
    .eq("user_id", me.user!.id).order("created_at", { ascending: false });

  const { data: verdicts } = await sb.from("genlayer_verdicts")
    .select("advisory_case_id,verdict,risk_level,transaction_hash").eq("user_id", me.user!.id);
  const vmap = new Map((verdicts ?? []).map(v => [v.advisory_case_id, v]));

  return (
    <AppShell section="Advisory cases" subtitle="All cases · status · verdicts">
      <div className="flex items-center justify-between mb-5">
        <h1 className="font-display text-3xl text-pearl">All cases</h1>
        <Link href="/cases/new" className="btn-primary text-sm">+ New case</Link>
      </div>

      {(cases ?? []).length === 0 ? (
        <div className="panel p-10 text-center text-sage">No advisory cases yet. Start with a new case.</div>
      ) : (
        <div className="panel overflow-hidden">
          <table className="os">
            <thead><tr>
              <th>Crop</th><th>Farm</th><th>Decision</th><th>Status</th><th>Verdict</th><th>Tx</th><th></th>
            </tr></thead>
            <tbody>
              {(cases ?? []).map(c => {
                const v = vmap.get(c.id);
                return (
                  <tr key={c.id}>
                    <td className="font-display text-pearl">{c.crop_type}</td>
                    <td className="text-pearl/80">{(c as any).farms?.name ?? "—"}</td>
                    <td className="text-pearl/80">{c.decision_type}</td>
                    <td><span className="badge badge-sensor">{c.status}</span></td>
                    <td className="text-pearl">{v?.verdict ?? <span className="text-sage">—</span>}</td>
                    <td><HashText value={v?.transaction_hash} kind="tx" /></td>
                    <td><Link href={`/cases/${c.id}`} className="text-biosignal">Open →</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
