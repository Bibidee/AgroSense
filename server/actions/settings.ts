"use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";

export async function updateNotificationPrefs(prefs: Record<string, boolean>) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const { error } = await sb.from("profiles")
    .update({ notification_prefs: prefs }).eq("user_id", me.user.id);
  if (error) return { ok: false, error: error.message };
  revalidatePath("/settings");
  return { ok: true };
}

// Bundle the user's full data into a JSON blob for download.
export async function exportUserData() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const uid = me.user.id;

  const [
    profileRes, walletRes, farmsRes, casesRes, evidenceRes,
    snapshotsRes, verdictsRes, activityRes, auditRes,
  ] = await Promise.all([
    sb.from("profiles").select("*").eq("user_id", uid).maybeSingle(),
    sb.from("wallets").select("id,address,created_at").eq("user_id", uid).maybeSingle(),
    sb.from("farms").select("*").eq("user_id", uid),
    sb.from("advisory_cases").select("*").eq("user_id", uid),
    sb.from("evidence_files").select("*").eq("user_id", uid),
    sb.from("data_snapshots").select("*").eq("user_id", uid),
    sb.from("genlayer_verdicts").select("*").eq("user_id", uid),
    sb.from("contract_activity_logs").select("*").eq("user_id", uid),
    sb.from("recovery_audit_logs").select("*").eq("user_id", uid),
  ]);

  return {
    ok: true,
    bundle: {
      exported_at: new Date().toISOString(),
      profile: profileRes.data,
      wallet: walletRes.data,
      farms: farmsRes.data ?? [],
      advisory_cases: casesRes.data ?? [],
      evidence_files: evidenceRes.data ?? [],
      data_snapshots: snapshotsRes.data ?? [],
      verdicts: verdictsRes.data ?? [],
      contract_activity: activityRes.data ?? [],
      recovery_audit: auditRes.data ?? [],
    },
  };
}

export async function markOnboardingComplete() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const { error } = await sb.from("profiles")
    .update({ onboarding_completed: true }).eq("user_id", me.user.id);
  if (error) return { ok: false, error: error.message };
  revalidatePath("/dashboard");
  return { ok: true };
}
