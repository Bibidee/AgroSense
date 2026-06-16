import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";
import { ConsensusBadge } from "@/components/Badges";
import { AGROSENSE_CONTRACT_ADDRESS, AGROSENSE_CONTRACT_NETWORK } from "@/lib/genlayer/contract";
import { AdminCaseActions } from "./AdminCaseActions";

export default async function AdminPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user!.id).maybeSingle();
  if (prof?.role !== "admin") redirect("/dashboard");

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,user_id,crop_type,status,created_at").order("created_at", { ascending: false }).limit(50);
  const { data: verdicts } = await sb.from("genlayer_verdicts")
    .select("*").order("created_at", { ascending: false }).limit(20);
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("*").order("created_at", { ascending: false }).limit(30);

  return (
    <AppShell section="Contract operations console" subtitle="Admin · GenLayer mirror">
      <div className="space-y-6">
        <div className="panel-violet p-5 relative scanline">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-sage">Source of truth contract</div>
              <div className="font-mono text-pearl break-all mt-1">{AGROSENSE_CONTRACT_ADDRESS}</div>
            </div>
            <ConsensusBadge label={AGROSENSE_CONTRACT_NETWORK} />
          </div>
        </div>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Case queue</div>
            <span className="badge badge-muted">{cases?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>Crop</th><th>Status</th><th>Created</th><th>User</th><th>Actions</th></tr></thead>
            <tbody>
              {(cases ?? []).map(c => (
                <tr key={c.id}>
                  <td className="font-display text-pearl">{c.crop_type}</td>
                  <td><span className="badge badge-sensor">{c.status}</span></td>
                  <td className="text-sage">{new Date(c.created_at).toLocaleString()}</td>
                  <td className="font-mono text-xs text-sage">{c.user_id.slice(0,8)}…</td>
                  <td><AdminCaseActions caseId={c.id} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <div className="font-display text-pearl text-xl mb-3">Mirrored verdicts</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(verdicts ?? []).map(v => (
              <div key={v.id} className="panel p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-pearl text-lg">{v.verdict}</div>
                  <ConsensusBadge label={v.consensus_status} />
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
                  <div><div className="text-[10px] uppercase text-sage">Risk</div><div className="text-pearl">{v.risk_level}</div></div>
                  <div><div className="text-[10px] uppercase text-sage">Plan</div><div className="text-pearl">{v.selected_plan}</div></div>
                </div>
                <div className="mt-3 flex flex-wrap gap-3"><HashText label="tx" value={v.transaction_hash} kind="tx" /><HashText label="case" value={v.advisory_case_id} /></div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Contract activity stream</div>
            <span className="badge badge-muted">{activity?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>When</th><th>Action</th><th>Status</th><th>Tx</th><th>Error</th></tr></thead>
            <tbody>
              {(activity ?? []).map(a => (
                <tr key={a.id}>
                  <td className="text-sage text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="text-pearl">{a.action}</td>
                  <td><span className={`badge ${a.status === "error" ? "badge-risk" : a.status === "submitted" ? "badge-sensor" : "badge-bio"}`}>{a.status}</span></td>
                  <td><HashText value={a.transaction_hash} kind="tx" /></td>
                  <td className="text-stormclay text-xs max-w-[260px] truncate">{a.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </AppShell>
  );
}
