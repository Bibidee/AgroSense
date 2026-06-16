"""
Stage 5 - Fix submit + verdict + evidence delete + sidebar + cases list.
Run:  python scripts/stage5_fixes.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

# ---------- explorer + chain config ----------
F["lib/genlayer/contract.ts"] = r"""// Single source of truth for the deployed AgroSenseAdvisory contract.
export const AGROSENSE_CONTRACT_ADDRESS =
  (process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ||
    "0x0eb53e72070Da3488128D4D10605e3Bb26E017f1") as `0x${string}`;

export const AGROSENSE_CONTRACT_NETWORK = "GenLayer StudioNet";
export const AGROSENSE_CHAIN_ID = 61999;
export const AGROSENSE_RPC_URL  = "https://studio.genlayer.com/api";
export const AGROSENSE_EXPLORER = "https://explorer-studio.genlayer.com";

export const txUrl = (hash?: string | null) =>
  hash ? `${AGROSENSE_EXPLORER}/tx/${hash}` : null;
export const addressUrl = (addr?: string | null) =>
  addr ? `${AGROSENSE_EXPLORER}/address/${addr}` : null;
"""

# ---------- GenLayer client: no fake consensus, real verdict only ----------
F["lib/genlayer/client.ts"] = r"""// GenLayer client wrapper. genlayer-js v0.10.x.
// Returns ONLY real on-chain data. No mock fallbacks. If validators have not
// produced a verdict yet, finalStatus = "awaiting_consensus" so the UI can
// render a true pending state.
import "server-only";
import { createClient, createAccount, chains } from "genlayer-js";
import { AGROSENSE_CONTRACT_ADDRESS } from "./contract";

const CONTRACT = AGROSENSE_CONTRACT_ADDRESS;

export interface AdvisoryPacket {
  advisoryId: string;
  farmRegion: string;
  cropType: string;
  advisoryQuestion: string;
  plantingWindow: string;
  weatherContext: string;
  marketContext: string;
  weatherUrl: string;
  marketUrl: string;
  soilEvidenceHash: string;
  uploadedEvidenceHash: string;
  userObservationText: string;
  backendProposedPlanA: string;
  backendProposedPlanB: string;
  backendProposedPlanC: string;
}

// Deployed AgroSenseAdvisory ABI surface. Source of truth: gen_getContractSchema.
export const AGROSENSE_METHODS = {
  submit_advisory: [
    "advisory_id","farm_region","crop_type","advisory_question","planting_window",
    "weather_context","market_context","weather_url","market_url",
    "soil_evidence_hash","uploaded_evidence_hash","user_observation_text",
    "backend_proposed_plan_a","backend_proposed_plan_b","backend_proposed_plan_c",
  ],
  get_verdict: ["advisory_id"],
} as const;

export interface VerdictResult {
  advisoryId: string;
  verdict: string | null;
  riskLevel: string | null;
  confidenceLabel: string | null;
  selectedPlan: string | null;
  reasoningSummary: string | null;
  evidenceDigest: string;
  consensusTimestamp: string;
  finalStatus: "consensus_reached" | "awaiting_consensus" | "submit_failed";
  transactionHash: string;
  contractAddress: string;
}

function makeClient() {
  if (!CONTRACT) throw new Error("Missing NEXT_PUBLIC_AGROSENSE_CONTRACT_ADDRESS");
  const privKey = process.env.GENLAYER_SUBMITTER_PRIVATE_KEY;
  if (!privKey) throw new Error("Missing GENLAYER_SUBMITTER_PRIVATE_KEY");
  const endpoint = process.env.GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
  const chain = chains.localnet;
  const account = createAccount(privKey as `0x${string}`);
  return createClient({ chain, endpoint, account } as any);
}

function isVerdictReady(v: any): boolean {
  return !!(v && typeof v === "object" && v.verdict && v.final_status === "consensus_reached");
}

export async function submitAdvisoryToGenLayer(packet: AdvisoryPacket): Promise<VerdictResult> {
  const client: any = makeClient();

  const args = [
    packet.advisoryId, packet.farmRegion, packet.cropType, packet.advisoryQuestion,
    packet.plantingWindow, packet.weatherContext, packet.marketContext,
    packet.weatherUrl, packet.marketUrl,
    packet.soilEvidenceHash, packet.uploadedEvidenceHash, packet.userObservationText,
    packet.backendProposedPlanA, packet.backendProposedPlanB, packet.backendProposedPlanC,
  ];
  if (args.length !== AGROSENSE_METHODS.submit_advisory.length) {
    throw new Error(`ABI mismatch: submit_advisory expects ${AGROSENSE_METHODS.submit_advisory.length} args, got ${args.length}`);
  }

  const txHash: string = await client.writeContract({
    address: CONTRACT, functionName: "submit_advisory", args, value: 0n,
  });
  if (!txHash || typeof txHash !== "string") throw new Error("GenLayer write returned no transaction hash");

  try { await client.waitForTransactionReceipt({ hash: txHash, retries: { count: 30, interval: 4000 } }); }
  catch { /* Studio may not implement receipts uniformly; continue */ }

  // Read verdict with a short poll. Up to 6 attempts spaced 5s apart.
  let v: any = null;
  for (let i = 0; i < 6; i++) {
    try {
      v = await client.readContract({
        address: CONTRACT, functionName: "get_verdict", args: [packet.advisoryId],
      });
      if (isVerdictReady(v)) break;
    } catch { /* keep retrying */ }
    await new Promise(r => setTimeout(r, 5000));
  }

  const ready = isVerdictReady(v);
  return {
    advisoryId: packet.advisoryId,
    verdict:           ready ? v.verdict ?? null : null,
    riskLevel:         ready ? v.risk_level ?? null : null,
    confidenceLabel:   ready ? v.confidence_label ?? null : null,
    selectedPlan:      ready ? v.selected_plan ?? null : null,
    reasoningSummary:  ready ? v.reasoning_summary ?? null : null,
    evidenceDigest:    ready ? v.evidence_digest ?? "" : `${packet.soilEvidenceHash.slice(0,12)}|${packet.uploadedEvidenceHash.slice(0,12)}`,
    consensusTimestamp: ready ? (v.consensus_timestamp || new Date().toISOString()) : "",
    finalStatus: ready ? "consensus_reached" : "awaiting_consensus",
    transactionHash: txHash,
    contractAddress: CONTRACT,
  };
}

// Re-read the verdict for a previously-submitted advisory.
export async function readVerdict(advisoryId: string) {
  const client: any = makeClient();
  try {
    const v = await client.readContract({
      address: CONTRACT, functionName: "get_verdict", args: [advisoryId],
    });
    if (!isVerdictReady(v)) return null;
    return v;
  } catch { return null; }
}
"""

# ---------- cases action: write what client returns; if pending, leave verdict NULL ----------
F["server/actions/cases.ts"] = r""""use server";
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

export async function submitToGenLayer(caseId: string) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

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
    });

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
"""

# ---------- evidence: add delete action ----------
F["server/actions/evidence.ts"] = r""""use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";
import { sha256Hex } from "@/lib/util/hash";

const MAX_BY_TYPE: Record<string, number> = {
  "image/jpeg": 2 * 1024 * 1024,
  "image/png":  2 * 1024 * 1024,
  "image/webp": 2 * 1024 * 1024,
  "application/pdf": 5 * 1024 * 1024,
  "application/json": 1 * 1024 * 1024,
};
const ALLOWED_EXT = ["jpg","jpeg","png","webp","pdf","json"];

export async function uploadEvidence(formData: FormData) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  const caseId = String(formData.get("caseId") ?? "");
  const file = formData.get("file") as File | null;
  if (!file || !caseId) return { ok: false, error: "Missing file or case id." };

  const ext = (file.name.split(".").pop() ?? "").toLowerCase();
  if (!ALLOWED_EXT.includes(ext)) return { ok: false, error: "File type not allowed." };

  const max = MAX_BY_TYPE[file.type];
  if (!max) return { ok: false, error: "MIME type not allowed." };
  if (file.size > max) return { ok: false, error: "File too large." };

  const { count } = await sb.from("evidence_files")
    .select("id", { count: "exact", head: true }).eq("advisory_case_id", caseId);
  if ((count ?? 0) >= 3) return { ok: false, error: "Maximum 3 evidence files per case." };

  const buf = Buffer.from(await file.arrayBuffer());
  const hash = sha256Hex(buf);
  const path = `${me.user.id}/${caseId}/${Date.now()}-${file.name}`;

  const { error: upErr } = await sb.storage.from("evidence").upload(path, buf, {
    contentType: file.type, upsert: false,
  });
  if (upErr) return { ok: false, error: upErr.message };

  const { data: signed } = await sb.storage.from("evidence").createSignedUrl(path, 60 * 60 * 24 * 7);

  const { error } = await sb.from("evidence_files").insert({
    user_id: me.user.id,
    advisory_case_id: caseId,
    file_url: signed?.signedUrl ?? "",
    file_path: path,
    file_bucket: "evidence",
    file_type: file.type,
    file_size: file.size,
    evidence_hash: hash,
    uploaded_by: me.user.id,
  });
  if (error) return { ok: false, error: error.message };

  await sb.from("advisory_cases").update({ status: "evidence_added" }).eq("id", caseId);
  revalidatePath(`/cases/${caseId}`);
  revalidatePath(`/evidence`);
  return { ok: true, hash };
}

export async function deleteEvidence(evidenceId: string) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  const { data: row } = await sb.from("evidence_files")
    .select("id, file_path, advisory_case_id").eq("id", evidenceId).eq("user_id", me.user.id).maybeSingle();
  if (!row) return { ok: false, error: "Evidence not found." };

  // RLS blocks deletes after a verdict exists for safety — check first.
  const { data: verdict } = await sb.from("genlayer_verdicts")
    .select("id").eq("advisory_case_id", row.advisory_case_id).maybeSingle();
  if (verdict) return { ok: false, error: "Cannot delete evidence after a verdict has been issued." };

  await sb.storage.from("evidence").remove([row.file_path]);
  const { error } = await sb.from("evidence_files").delete().eq("id", evidenceId);
  if (error) return { ok: false, error: error.message };

  revalidatePath(`/cases/${row.advisory_case_id}`);
  revalidatePath(`/evidence`);
  return { ok: true };
}
"""

# ---------- HashText: optional clickable explorer link ----------
F["components/HashText.tsx"] = r"""import Link from "next/link";
import { txUrl, addressUrl } from "@/lib/genlayer/contract";

export function HashText({
  value, label, kind,
}: { value?: string | null; label?: string; kind?: "tx" | "address" }) {
  if (!value) return <span className="font-mono text-xs text-sage">—</span>;
  const short = value.length > 18 ? `${value.slice(0,8)}…${value.slice(-6)}` : value;
  const href = kind === "tx" ? txUrl(value) : kind === "address" ? addressUrl(value) : null;
  const inner = (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs">
      {label && <span className="text-sage uppercase tracking-wider text-[10px]">{label}</span>}
      <span className={href ? "text-sensor underline-offset-2 hover:underline" : "text-pearl/90"}>{short}</span>
    </span>
  );
  return href ? <Link href={href} target="_blank" rel="noreferrer">{inner}</Link> : inner;
}
"""

# ---------- VerdictCapsule: real pending vs real verdict; never contradict ----------
F["components/VerdictCapsule.tsx"] = r"""import { ConsensusBadge, RiskBadge, ActionWindowBadge } from "./Badges";
import { HashText } from "./HashText";

type Status = "not_submitted" | "awaiting_consensus" | "consensus_reached";

export function VerdictCapsule({
  v, status = "not_submitted", txHash,
}: { v?: any; status?: Status; txHash?: string | null }) {
  if (status === "not_submitted" || (!v && status === "consensus_reached")) {
    return (
      <div className="panel p-6 relative scanline">
        <div className="text-[10px] uppercase tracking-wider text-sage">Latest verdict</div>
        <div className="font-display text-2xl text-pearl/60 mt-2">Not submitted</div>
        <div className="text-sage text-sm mt-1">Submit the advisory packet to GenLayer to request a consensus verdict.</div>
      </div>
    );
  }
  if (status === "awaiting_consensus" || !v) {
    return (
      <div className="panel p-6 relative scanline">
        <div className="flex items-center justify-between">
          <div className="text-[10px] uppercase tracking-wider text-sage">Consensus verdict</div>
          <span className="badge badge-sensor"><i className="dot dot-sensor pulse-consensus"></i>Awaiting consensus</span>
        </div>
        <div className="font-display text-3xl text-pearl mt-3">Validators reasoning…</div>
        <p className="text-sage text-sm mt-2">Transaction submitted. Verdict will appear here when validators converge on-chain.</p>
        {txHash && (
          <div className="mt-4 pt-3 border-t border-white/10">
            <HashText label="tx" value={txHash} kind="tx" />
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="panel-violet p-6 relative scanline lift">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-sage">Consensus verdict</div>
        <ConsensusBadge label={v.consensus_status ?? "Validated"} />
      </div>
      <div className="font-display text-4xl text-pearl mt-3">{v.verdict}</div>
      <div className="flex flex-wrap gap-2 mt-3">
        {v.risk_level && <RiskBadge level={v.risk_level} />}
        {v.confidence_label && <span className="badge badge-bio">{v.confidence_label} confidence</span>}
        <ActionWindowBadge window="Review window 5d" />
      </div>
      {v.reasoning_summary && (
        <p className="text-sm text-pearl/80 mt-4 leading-relaxed">{v.reasoning_summary}</p>
      )}
      <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-4">
        <HashText label="tx" value={v.transaction_hash} kind="tx" />
        <HashText label="contract" value={v.contract_address} kind="address" />
        <HashText label="digest" value={v.evidence_digest} />
      </div>
    </div>
  );
}
"""

# ---------- GenLayerConsensusPanel: status sourced from same truth ----------
F["components/GenLayerConsensusPanel.tsx"] = r"""import { ConsensusBadge, SourceOfTruthBadge } from "./Badges";
import { HashText } from "./HashText";

type Status = "not_submitted" | "awaiting_consensus" | "consensus_reached";

export function GenLayerConsensusPanel({
  v, status = "not_submitted", txHash,
}: { v?: any; status?: Status; txHash?: string | null }) {
  const label =
    status === "consensus_reached" ? "Consensus reached"
    : status === "awaiting_consensus" ? "Awaiting consensus"
    : "Not submitted";
  return (
    <div className="panel p-6 relative scanline">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer Adjudication</div>
          <div className="font-display text-pearl text-xl mt-1">Consensus module</div>
        </div>
        <SourceOfTruthBadge />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-5 text-sm">
        <div><div className="text-[10px] uppercase text-sage">Network</div><div className="text-pearl">StudioNet</div></div>
        <div><div className="text-[10px] uppercase text-sage">Status</div><div><ConsensusBadge label={label} /></div></div>
        <div><div className="text-[10px] uppercase text-sage">Contract</div><HashText value={v?.contract_address} kind="address" /></div>
        <div><div className="text-[10px] uppercase text-sage">Advisory ID</div><HashText value={v?.advisory_id_on_chain} /></div>
        <div className="col-span-2"><div className="text-[10px] uppercase text-sage">Transaction</div><HashText value={v?.transaction_hash ?? txHash} kind="tx" /></div>
      </div>
    </div>
  );
}
"""

# ---------- Sidebar: add Cases ----------
F["components/CommandRail.tsx"] = r""""use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./Brand";
import { ConsensusBadge } from "./Badges";

const NAV = [
  { href: "/dashboard", label: "Dashboard", glyph: "◎" },
  { href: "/farms",     label: "Farms",     glyph: "▦" },
  { href: "/cases/new", label: "New case",  glyph: "+" },
  { href: "/cases",     label: "Cases",     glyph: "≡" },
  { href: "/evidence",  label: "Evidence",  glyph: "▣" },
  { href: "/profile",   label: "Profile",   glyph: "◐" },
  { href: "/settings",  label: "Settings",  glyph: "⚙" },
];

export function CommandRail({ admin, email, wallet }: { admin?: boolean; email?: string | null; wallet?: string | null }) {
  const path = usePathname();
  return (
    <aside className="hidden md:flex flex-col w-64 shrink-0 h-screen sticky top-0 border-r border-white/5 bg-graphite/60 backdrop-blur-md">
      <div className="px-5 pt-5 pb-4"><Brand /></div>
      <div className="px-3 pt-2 pb-3"><div className="hr" /></div>
      <nav className="flex-1 px-3 space-y-1">
        {NAV.map(n => {
          const active = path === n.href || (n.href !== "/dashboard" && path?.startsWith(n.href + "/"));
          const exact  = path === n.href;
          const on = exact || active;
          return (
            <Link key={n.href} href={n.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition
                ${on ? "bg-biosignal/10 text-biosignal border border-biosignal/30 shadow-glow"
                     : "text-pearl/80 hover:text-pearl hover:bg-white/5 border border-transparent"}`}>
              <span className={`w-6 h-6 grid place-items-center rounded-md text-xs ${on ? "bg-biosignal/20" : "bg-white/5"}`}>{n.glyph}</span>
              <span>{n.label}</span>
              {on && <span className="ml-auto dot dot-bio"></span>}
            </Link>
          );
        })}
        {admin && (
          <Link href="/admin"
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm mt-3
              ${path?.startsWith("/admin") ? "bg-consensus/15 text-pearl border border-consensus/40 shadow-violet" : "text-pearl/80 hover:bg-white/5 border border-transparent"}`}>
            <span className="w-6 h-6 grid place-items-center rounded-md text-xs bg-consensus/20">◈</span>
            <span>Admin console</span>
          </Link>
        )}
      </nav>
      <div className="px-4 pb-3">
        <div className="panel-violet p-3 text-xs">
          <ConsensusBadge label="GenLayer StudioNet" />
          <div className="font-mono text-[10px] text-sage mt-2 break-all">0x0eb53e72…E017f1</div>
        </div>
      </div>
      <div className="px-3 pb-4">
        <div className="rounded-xl border border-white/10 bg-obsidian/70 p-3">
          <div className="text-[10px] uppercase tracking-wider text-sage">Operator</div>
          <div className="text-sm text-pearl truncate">{email ?? "—"}</div>
          {wallet && <div className="font-mono text-[10px] text-sage mt-1 break-all">{wallet.slice(0,10)}…{wallet.slice(-6)}</div>}
        </div>
      </div>
    </aside>
  );
}
"""

# ---------- /cases list page ----------
F["app/cases/page.tsx"] = r"""import Link from "next/link";
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
"""

# ---------- Case detail page rewrite ----------
F["app/cases/[id]/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { uploadEvidence } from "@/server/actions/evidence";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { HashText } from "@/components/HashText";
import { SubmitButton } from "./SubmitButton";
import { RefreshVerdictButton } from "./RefreshVerdictButton";
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
"""

F["app/cases/[id]/RefreshVerdictButton.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { refreshVerdict } from "@/server/actions/cases";

export function RefreshVerdictButton({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();
  const router = useRouter();
  return (
    <>
      <button type="button" disabled={pending}
        onClick={() => {
          setMsg(undefined);
          start(async () => {
            try {
              const r = await refreshVerdict(caseId);
              if (!r.ok) setMsg(r.error || "No verdict yet on-chain.");
              else { setMsg("Verdict synced."); router.refresh(); }
            } catch (e) { setMsg(e instanceof Error ? e.message : "Refresh failed"); }
          });
        }}
        className="btn-ghost w-full disabled:opacity-60">
        {pending ? "Checking on-chain…" : "Refresh verdict"}
      </button>
      {msg && <div className="text-xs text-sage">{msg}</div>}
    </>
  );
}
"""

F["app/cases/[id]/DeleteEvidenceButton.tsx"] = r""""use client";
import { useTransition, useState } from "react";
import { useRouter } from "next/navigation";
import { deleteEvidence } from "@/server/actions/evidence";

export function DeleteEvidenceButton({ evidenceId }: { evidenceId: string }) {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  const router = useRouter();
  return (
    <>
      <button type="button" disabled={pending}
        onClick={() => {
          setErr(undefined);
          start(async () => {
            const r = await deleteEvidence(evidenceId);
            if (!r.ok) setErr(r.error || "Delete failed");
            else router.refresh();
          });
        }}
        className="text-xs text-stormclay hover:text-stormclay/80 px-2 py-1 rounded-md border border-stormclay/30 disabled:opacity-50">
        {pending ? "Removing…" : "Remove"}
      </button>
      {err && <span className="text-[10px] text-stormclay ml-2">{err}</span>}
    </>
  );
}
"""

# ---------- SubmitButton: real submit, real tx, refresh page ----------
F["app/cases/[id]/SubmitButton.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { submitToGenLayer } from "@/server/actions/cases";
import { txUrl } from "@/lib/genlayer/contract";

export function SubmitButton({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  const [okTx, setOkTx] = useState<string>();
  const router = useRouter();

  function onClick() {
    setErr(undefined); setOkTx(undefined);
    console.log("[AgroSense] Submit to GenLayer clicked, caseId =", caseId);
    start(async () => {
      try {
        const r = await submitToGenLayer(caseId);
        console.log("[AgroSense] Submit result:", r);
        if (!(r as any)?.ok) {
          setErr((r as any)?.error || "Submission failed");
          return;
        }
        setOkTx((r as any).txHash);
        router.refresh();
      } catch (e) {
        console.error("[AgroSense] Submit threw:", e);
        setErr(e instanceof Error ? e.message : "Submission failed");
      }
    });
  }

  return (
    <div className="mt-4 space-y-3">
      <button type="button" onClick={onClick} disabled={pending}
        className="btn-violet w-full disabled:opacity-60 disabled:cursor-not-allowed">
        {pending ? "Submitting to validators…" : "Submit to GenLayer →"}
      </button>
      {okTx && (
        <div className="rounded-xl border border-biosignal/40 bg-biosignal/10 p-3 text-sm text-pearl">
          <div className="font-display text-biosignal">Submitted</div>
          <a href={txUrl(okTx)!} target="_blank" rel="noreferrer" className="font-mono text-xs text-sensor underline-offset-2 hover:underline break-all">
            View tx on explorer · {okTx.slice(0,10)}…{okTx.slice(-6)}
          </a>
        </div>
      )}
      {err && (
        <div className="rounded-xl border border-stormclay/40 bg-stormclay/10 p-3 text-sm text-pearl">
          <div className="font-display text-stormclay">Submit failed</div>
          <div className="mt-1 text-pearl/80 break-words">{err}</div>
        </div>
      )}
    </div>
  );
}
"""

# ---------- Dashboard: same status derivation ----------
F["app/dashboard/page.tsx"] = r"""import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { WeatherRiskOrb } from "@/components/WeatherRiskOrb";
import { SignalStrip } from "@/components/SignalStrip";
import { EvidenceStrengthMeter } from "@/components/EvidenceStrengthMeter";
import { CropWindowTimeline } from "@/components/CropWindowTimeline";
import { ContractActivityStream } from "@/components/ContractActivityStream";
import { LiveBadge } from "@/components/Badges";

export default async function DashboardPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const userId = me.user!.id;

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,crop_type,status,created_at,decision_type").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(8);
  const { data: latest } = await sb.from("genlayer_verdicts")
    .select("*").eq("user_id", userId).order("created_at", { ascending: false }).limit(1).maybeSingle();
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("action,status,transaction_hash,created_at").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(5);

  return (
    <AppShell section="Mission control" subtitle="Live agricultural decision OS">
      <div className="space-y-6">
        <SignalStrip />

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-7">
            <VerdictCapsule v={latest} status={latest ? "consensus_reached" : "not_submitted"} />
          </div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-2"><WeatherRiskOrb level="moderate" label="Mixed rainfall" /></div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-3">
            <GenLayerConsensusPanel v={latest} status={latest ? "consensus_reached" : "not_submitted"} />
          </div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8">
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between px-5 pt-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-sage">Active case matrix</div>
                  <div className="font-display text-pearl text-lg">Recent advisories</div>
                </div>
                <div className="flex items-center gap-2">
                  <Link href="/cases" className="btn-ghost text-sm">All cases</Link>
                  <Link href="/cases/new" className="btn-primary text-sm">+ New case</Link>
                </div>
              </div>
              <table className="os mt-3">
                <thead><tr><th>Crop</th><th>Decision</th><th>Status</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {(cases ?? []).length === 0 && (
                    <tr><td colSpan={5} className="text-center text-sage py-10">No cases yet. Open a new advisory to engage GenLayer validators.</td></tr>
                  )}
                  {(cases ?? []).map(c => (
                    <tr key={c.id}>
                      <td className="font-display text-pearl">{c.crop_type}</td>
                      <td className="text-pearl/80">{c.decision_type}</td>
                      <td><span className="badge badge-sensor">{c.status}</span></td>
                      <td className="text-sage">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td><Link href={`/cases/${c.id}`} className="text-biosignal">Open →</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4"><EvidenceStrengthMeter score={latest ? 78 : 35} /></div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><CropWindowTimeline /></div>
          <div className="col-span-12 lg:col-span-4"><ContractActivityStream items={activity ?? []} /></div>
        </div>
      </div>
    </AppShell>
  );
}
"""

# ---------- Admin: use kind=tx for hash links ----------
# (Leave admin as-is; HashText already detects via prop. Optionally pass kind.)

# ---------- Demo: feed real-shape verdict ----------
F["app/demo/page.tsx"] = r"""import { VerdictCapsule } from "@/components/VerdictCapsule";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { AGROSENSE_CONTRACT_ADDRESS } from "@/lib/genlayer/contract";

const sample = {
  verdict: "Delay planting",
  risk_level: "High rainfall",
  confidence_label: "Strong",
  selected_plan: "B — Delay planting",
  consensus_status: "Validated by GenLayer",
  contract_address: AGROSENSE_CONTRACT_ADDRESS,
  transaction_hash: "0xdemo7f1c8ab0000000000000000000000000000000be02",
  advisory_id_on_chain: "demo-1",
  evidence_digest: "soil:9af2b1e7|files:c8ee3d10",
  reasoning_summary:
    "Validators independently reasoned that 7-day rainfall risk combined with incomplete soil confidence makes immediate planting unsafe. Delay is the most defensible action.",
};

export default function Demo() {
  return (
    <main className="min-h-screen bg-field-grid p-10 space-y-6 max-w-6xl mx-auto">
      <div>
        <span className="badge badge-consensus">Demo · Placeholder data (not on-chain)</span>
        <h1 className="font-display text-4xl text-pearl mt-3">Consensus Verdict Terminal</h1>
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7"><VerdictCapsule v={sample} status="consensus_reached" /></div>
        <div className="col-span-12 lg:col-span-5"><GenLayerConsensusPanel v={sample} status="consensus_reached" /></div>
      </div>
    </main>
  );
}
"""

def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage5] wrote {n} files")

if __name__ == "__main__":
    main()
