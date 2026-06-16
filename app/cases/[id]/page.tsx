import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { uploadEvidence } from "@/server/actions/evidence";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { HashText } from "@/components/HashText";
import { SubmitButton } from "./SubmitButton";
import { RefreshVerdictButton } from "./RefreshVerdictButton";
import { AutoPoll } from "./AutoPoll";
import { DeleteEvidenceButton } from "./DeleteEvidenceButton";

type Status = "not_submitted" | "awaiting_consensus" | "consensus_reached";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: c } = await sb.from("advisory_cases")
    .select("*, farms(name,country,region)").eq("id", id).eq("user_id", me.user!.id).maybeSingle();
  if (!c) redirect("/dashboard");
  const { data: ev } = await sb.from("evidence_files").select("*").eq("advisory_case_id", id).order("created_at", { ascending: true });
  const { data: verdict } = await sb.from("genlayer_verdicts")
    .select("*").eq("advisory_case_id", id).order("created_at", { ascending: false }).maybeSingle();
  const { data: lastActivity } = await sb.from("contract_activity_logs")
    .select("transaction_hash").eq("advisory_case_id", id)
    .not("transaction_hash", "is", null)
    .order("created_at", { ascending: false }).limit(1).maybeSingle();

  // Derive a single status from real data. No contradictions.
  const status: Status =
    verdict ? "consensus_reached"
    : (c.status === "submitted" || c.status === "consensus_pending") && lastActivity?.transaction_hash ? "awaiting_consensus"
    : "not_submitted";
  const txHash = verdict?.transaction_hash ?? lastActivity?.transaction_hash ?? null;

  async function uploadAction(fd: FormData) {
    "use server";
    const r = await uploadEvidence(fd);
    if (!r.ok) console.error("[uploadEvidence]", r.error);
  }

  return (
    <AppShell section={status === "consensus_reached" ? "Consensus Verdict Terminal" : "Advisory Packet Builder"} subtitle={`${c.crop_type} · ${c.decision_type}`}>
      <div className="space-y-6">
        {/* HERO */}
        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><VerdictCapsule v={verdict} status={status} txHash={txHash} /></div>
          <div className="col-span-12 lg:col-span-4"><GenLayerConsensusPanel v={verdict} status={status} txHash={txHash} /></div>
        </div>

        {/* CASE BODY */}
        <div className="grid grid-cols-12 gap-5">
          <section className="col-span-12 lg:col-span-5 panel p-5">
            <div className="text-[10px] uppercase tracking-wider text-sage">Advisory question</div>
            <p className="text-pearl mt-2 leading-relaxed">{c.advisory_question}</p>
            <div className="hr my-4" />
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Cell k="Farm"   v={(c as any).farms?.name ?? "—"} />
              <Cell k="Region" v={`${(c as any).farms?.region ?? ""} ${(c as any).farms?.country ?? ""}`} />
              <Cell k="Crop"   v={c.crop_type} />
              <Cell k="Window" v={c.planting_window ?? "—"} />
            </div>
            {c.user_observation && (
              <>
                <div className="hr my-4" />
                <div className="text-[10px] uppercase tracking-wider text-sage">Field observation</div>
                <p className="text-pearl/80 text-sm mt-2 leading-relaxed">{c.user_observation}</p>
              </>
            )}
          </section>

          <section className="col-span-12 lg:col-span-4 panel p-5">
            <div className="flex items-center justify-between">
              <div className="text-[10px] uppercase tracking-wider text-sage">Evidence vault</div>
              <span className="badge badge-muted">{ev?.length ?? 0} / 3</span>
            </div>
            <ul className="mt-3 space-y-2">
              {(ev ?? []).map(e => (
                <li key={e.id} className="rounded-xl border border-white/5 bg-obsidian/40 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-mono text-[11px] text-pearl/80 break-all min-w-0 flex-1">{e.file_path}</div>
                    {!verdict && <DeleteEvidenceButton evidenceId={e.id} />}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    <span className="badge badge-muted">{e.file_type.split("/").pop()?.toUpperCase()}</span>
                    <HashText label="sha256" value={e.evidence_hash} />
                  </div>
                </li>
              ))}
              {(ev ?? []).length === 0 && <li className="text-sage text-sm">No evidence attached yet.</li>}
            </ul>
            {(ev?.length ?? 0) < 3 && !verdict && (
              <form action={uploadAction} className="mt-3 flex flex-col gap-2">
                <input type="hidden" name="caseId" value={id} />
                <input type="file" name="file" required accept=".jpg,.jpeg,.png,.webp,.pdf,.json" className="text-sm text-sage file:btn-ghost file:mr-3 file:bg-white/5 file:border file:border-white/10 file:rounded-lg file:text-pearl" />
                <button className="btn-ghost">Attach evidence</button>
              </form>
            )}
          </section>

          <section className="col-span-12 lg:col-span-3 panel-violet p-5 relative scanline">
            <div className="text-[10px] uppercase tracking-wider text-sage">Adjudication</div>
            <div className="font-display text-pearl text-xl mt-1">GenLayer submit</div>
            <p className="text-sage text-xs mt-2">When ready, the advisory packet is sent to the AgroSenseAdvisory contract. The verdict is produced by validator consensus.</p>
            {status === "not_submitted" && <SubmitButton caseId={id} />}
            {status === "awaiting_consensus" && (
              <div className="mt-4 space-y-3">
                <span className="badge badge-sensor"><i className="dot dot-sensor pulse-consensus"></i>Awaiting consensus</span>
                <RefreshVerdictButton caseId={id} />
                <AutoPoll caseId={id} enabled />
              </div>
            )}
            {status === "consensus_reached" && (
              <div className="mt-4"><span className="badge badge-consensus">Verdict issued</span></div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}

function Cell({ k, v }: { k: string; v: string }) {
  return <div><div className="text-[10px] uppercase text-sage">{k}</div><div className="text-pearl mt-1">{v}</div></div>;
}
