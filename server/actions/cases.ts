"use server";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { advisoryCaseSchema } from "@/lib/validation/schemas";
import { submitAdvisoryToGenLayer, readVerdict } from "@/lib/genlayer/client";
import { AGROSENSE_CONTRACT_ADDRESS } from "@/lib/genlayer/contract";
import { sha256Hex } from "@/lib/util/hash";

export async function createAdvisoryCase(formData: FormData) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  const parsed = advisoryCaseSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { ok: false, error: "Invalid advisory inputs." };
  const v = parsed.data;

  const { data: row, error } = await sb.from("advisory_cases").insert({
    user_id: me.user.id,
    farm_id: v.farmId,
    crop_type: v.cropType,
    advisory_question: v.advisoryQuestion,
    decision_type: v.decisionType,
    planting_window: v.plantingWindow ?? null,
    user_observation: v.userObservation ?? null,
  }).select("id").single();
  if (error || !row) return { ok: false, error: error?.message ?? "Failed to create case." };

  if (v.weatherContext) {
    await sb.from("data_snapshots").insert({
      user_id: me.user.id, advisory_case_id: row.id,
      source_type: "weather", snapshot_json: { text: v.weatherContext },
      snapshot_hash: sha256Hex(v.weatherContext),
    });
  }
  if (v.marketContext) {
    await sb.from("data_snapshots").insert({
      user_id: me.user.id, advisory_case_id: row.id,
      source_type: "market", snapshot_json: { text: v.marketContext },
      snapshot_hash: sha256Hex(v.marketContext),
    });
  }

  redirect(`/cases/${row.id}`);
}

export async function submitToGenLayer(caseId: string, password: string) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  if (!password) return { ok: false, error: "Password required to unlock your wallet." };

  // ---- Re-auth + unwrap the user's embedded wallet (no dev key) ----
  const { error: reErr } = await sb.auth.signInWithPassword({ email: me.user.email!, password });
  if (reErr) return { ok: false, error: "Password incorrect." };

  const admin0 = supabaseAdmin();
  const { data: wallet } = await admin0.from("wallets")
    .select("id, encrypted_private_key").eq("user_id", me.user.id).maybeSingle();
  if (!wallet) return { ok: false, error: "Embedded wallet not found." };
  const { data: pwWrap } = await admin0.from("wallet_key_wraps")
    .select("encrypted_wallet_key, salt").eq("wallet_id", wallet.id).eq("method","password").maybeSingle();
  if (!pwWrap) return { ok: false, error: "Wallet password wrap missing." };

  const { unwrapWek, decryptPrivateKey } = await import("@/lib/crypto/wallet");
  let userPrivKey: `0x${string}`;
  try {
    const wek = unwrapWek(password, {
      encryptedWalletKey: pwWrap.encrypted_wallet_key, salt: pwWrap.salt,
    });
    userPrivKey = decryptPrivateKey(wek, wallet.encrypted_private_key);
  } catch {
    return { ok: false, error: "Failed to unlock embedded wallet." };
  }

  const { data: c } = await sb.from("advisory_cases")
    .select("*, farms!inner(name,country,region)")
    .eq("id", caseId).eq("user_id", me.user.id).maybeSingle();
  if (!c) return { ok: false, error: "Case not found." };

  const { data: snaps } = await sb.from("data_snapshots")
    .select("source_type, snapshot_json, snapshot_hash").eq("advisory_case_id", caseId);
  const { data: ev } = await sb.from("evidence_files")
    .select("evidence_hash").eq("advisory_case_id", caseId);

  const weather = snaps?.find(s => s.source_type === "weather")?.snapshot_json?.text ?? "";
  const market  = snaps?.find(s => s.source_type === "market")?.snapshot_json?.text ?? "";
  const soilHash   = snaps?.find(s => s.source_type === "soil")?.snapshot_hash ?? sha256Hex("none");
  const uploadHash = sha256Hex((ev ?? []).map(e => e.evidence_hash).join("|") || "none");

  const admin = supabaseAdmin();
  await admin.from("contract_activity_logs").insert({
    user_id: me.user.id, advisory_case_id: caseId,
    contract_address: AGROSENSE_CONTRACT_ADDRESS,
    action: "submit_advisory", status: "submitted",
  });
  await sb.from("advisory_cases").update({
    status: "submitted", submitted_to_genlayer_at: new Date().toISOString(),
  }).eq("id", caseId);

  try {
    const r = await submitAdvisoryToGenLayer({
      advisoryId: caseId,
      farmRegion: `${(c as any).farms.region ?? ""}, ${(c as any).farms.country}`,
      cropType: c.crop_type,
      advisoryQuestion: c.advisory_question,
      plantingWindow: c.planting_window ?? "",
      weatherContext: weather,
      marketContext: market,
      weatherUrl: "",
      marketUrl: "",
      soilEvidenceHash: soilHash,
      uploadedEvidenceHash: uploadHash,
      userObservationText: c.user_observation ?? "",
      backendProposedPlanA: c.proposed_plan_a,
      backendProposedPlanB: c.proposed_plan_b,
      backendProposedPlanC: c.proposed_plan_c,
    }, userPrivKey);

    if (r.finalStatus === "consensus_reached" && r.verdict) {
      await admin.from("genlayer_verdicts").insert({
        user_id: me.user.id,
        advisory_case_id: caseId,
        contract_address: r.contractAddress,
        transaction_hash: r.transactionHash,
        advisory_id_on_chain: r.advisoryId,
        verdict: r.verdict,
        risk_level: r.riskLevel ?? "",
        confidence_label: r.confidenceLabel ?? "",
        selected_plan: r.selectedPlan ?? "",
        reasoning_summary: r.reasoningSummary ?? "",
        evidence_digest: r.evidenceDigest,
        consensus_status: r.finalStatus,
        consensus_timestamp: r.consensusTimestamp || new Date().toISOString(),
      });
      await sb.from("advisory_cases").update({ status: "verdict_issued" }).eq("id", caseId);
    } else {
      // Submitted on-chain but consensus not yet finalized. Mark pending.
      await sb.from("advisory_cases").update({ status: "consensus_pending" }).eq("id", caseId);
    }

    await admin.from("contract_activity_logs").insert({
      user_id: me.user.id, advisory_case_id: caseId,
      contract_address: r.contractAddress, transaction_hash: r.transactionHash,
      action: r.finalStatus === "consensus_reached" ? "verdict_received" : "awaiting_consensus",
      status: "ok",
    });
    revalidatePath(`/cases/${caseId}`);
    revalidatePath(`/cases`);
    revalidatePath(`/dashboard`);
    return { ok: true, txHash: r.transactionHash, finalStatus: r.finalStatus, verdict: r.verdict };
  } catch (e: any) {
    await admin.from("contract_activity_logs").insert({
      user_id: me.user.id, advisory_case_id: caseId,
      contract_address: AGROSENSE_CONTRACT_ADDRESS,
      action: "submit_advisory", status: "error", error_message: String(e?.message ?? e),
    });
    return { ok: false, error: String(e?.message ?? e) };
  }
}

// Manual re-fetch from chain if verdict was pending earlier.
export async function refreshVerdict(caseId: string) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const v: any = await readVerdict(caseId);
  if (!v) return { ok: false, error: "No verdict on-chain yet." };
  const admin = supabaseAdmin();
  const { data: existing } = await admin.from("genlayer_verdicts").select("id").eq("advisory_case_id", caseId).maybeSingle();
  if (existing) return { ok: true, alreadyMirrored: true };
  const { data: log } = await admin.from("contract_activity_logs")
    .select("transaction_hash").eq("advisory_case_id", caseId).order("created_at", { ascending: false }).limit(1).maybeSingle();
  await admin.from("genlayer_verdicts").insert({
    user_id: me.user.id,
    advisory_case_id: caseId,
    contract_address: AGROSENSE_CONTRACT_ADDRESS,
    transaction_hash: log?.transaction_hash ?? "",
    advisory_id_on_chain: caseId,
    verdict: v.verdict,
    risk_level: v.risk_level ?? "",
    confidence_label: v.confidence_label ?? "",
    selected_plan: v.selected_plan ?? "",
    reasoning_summary: v.reasoning_summary ?? "",
    evidence_digest: v.evidence_digest ?? "",
    consensus_status: "consensus_reached",
    consensus_timestamp: v.consensus_timestamp || new Date().toISOString(),
  });
  await sb.from("advisory_cases").update({ status: "verdict_issued" }).eq("id", caseId);
  revalidatePath(`/cases/${caseId}`);
  return { ok: true };
}
