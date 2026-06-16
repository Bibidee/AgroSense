"use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";

type SB = Awaited<ReturnType<typeof supabaseServer>>;
type AdminCtx =
  | { ok: false; error: string }
  | { ok: true; sb: SB; userId: string };

async function assertAdmin(): Promise<AdminCtx> {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user.id).maybeSingle();
  if (prof?.role !== "admin") return { ok: false, error: "Admin only." };
  return { ok: true, sb, userId: me.user.id };
}

// Replay clears the mirrored verdict and resets case status so the operator can re-submit.
// (Admins can't sign with the user's wallet — re-submission must come from the operator.)
export async function replayCase(caseId: string) {
  const a = await assertAdmin();
  if (!a.ok) return a;
  const admin = supabaseAdmin();
  await admin.from("genlayer_verdicts").delete().eq("advisory_case_id", caseId);
  await a.sb.from("advisory_cases").update({
    status: "ready", submitted_to_genlayer_at: null,
  }).eq("id", caseId);
  await admin.from("contract_activity_logs").insert({
    user_id: a.userId, advisory_case_id: caseId,
    contract_address: process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ?? "",
    action: "admin_replay_requested", status: "ok",
  });
  revalidatePath("/admin");
  revalidatePath(`/cases/${caseId}`);
  return { ok: true };
}

// Export the full advisory packet (case + farm + snapshots + evidence) as JSON.
export async function exportAdvisoryPacket(caseId: string) {
  const a = await assertAdmin();
  if (!a.ok) return a;
  const [c, ev, snaps, verdict] = await Promise.all([
    a.sb.from("advisory_cases").select("*, farms(*)").eq("id", caseId).maybeSingle(),
    a.sb.from("evidence_files").select("*").eq("advisory_case_id", caseId),
    a.sb.from("data_snapshots").select("*").eq("advisory_case_id", caseId),
    a.sb.from("genlayer_verdicts").select("*").eq("advisory_case_id", caseId).maybeSingle(),
  ]);
  return {
    ok: true,
    bundle: {
      exported_at: new Date().toISOString(),
      case: c.data,
      evidence: ev.data ?? [],
      snapshots: snaps.data ?? [],
      verdict: verdict.data ?? null,
    },
  };
}
