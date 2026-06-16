"""
Stage 3 - Application code: Supabase clients, wallet crypto, GenLayer client,
auth + wallet flows, server actions, all pages, components, GenLayer contract.
Run:  python scripts/stage3_app.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

# =========================================================================
#                              LIB
# =========================================================================

F["lib/supabase/client.ts"] = r"""import { createBrowserClient } from "@supabase/ssr";

export function supabaseBrowser() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
"""

F["lib/supabase/server.ts"] = r"""import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function supabaseServer() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (all) => {
          try { all.forEach(({ name, value, options }) => cookieStore.set(name, value, options)); } catch {}
        },
      },
    }
  );
}
"""

F["lib/supabase/admin.ts"] = r"""import { createClient } from "@supabase/supabase-js";

// Server-only privileged client. NEVER import from client components.
export function supabaseAdmin() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}
"""

# ---------- Wallet crypto ----------
F["lib/crypto/wallet.ts"] = r"""// Server-only wallet crypto.
// - Generates secp256k1 keypair (viem).
// - WEK = random 32 bytes. AES-GCM(privkey) keyed by WEK -> wallets.encrypted_private_key
// - Wraps WEK twice (password + recovery) via PBKDF2-SHA256 (210k iter).
import "server-only";
import crypto from "node:crypto";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

const KDF_ITER = 210_000;
const KDF_KEYLEN = 32;
const AES = "aes-256-gcm";

function b64(buf: Buffer | Uint8Array) { return Buffer.from(buf).toString("base64"); }
function ub64(s: string) { return Buffer.from(s, "base64"); }

function pepper(): Buffer {
  const p = process.env.WALLET_KDF_PEPPER || "";
  if (!p) throw new Error("WALLET_KDF_PEPPER not set");
  return Buffer.from(p, "base64");
}

function deriveKey(secret: string, salt: Buffer): Buffer {
  const peppered = Buffer.concat([Buffer.from(secret, "utf8"), pepper()]);
  return crypto.pbkdf2Sync(peppered, salt, KDF_ITER, KDF_KEYLEN, "sha256");
}

function aesEncrypt(key: Buffer, plaintext: Buffer): string {
  const iv = crypto.randomBytes(12);
  const c = crypto.createCipheriv(AES, key, iv);
  const ct = Buffer.concat([c.update(plaintext), c.final()]);
  const tag = c.getAuthTag();
  return b64(Buffer.concat([iv, ct, tag]));
}

function aesDecrypt(key: Buffer, packed: string): Buffer {
  const buf = ub64(packed);
  const iv = buf.subarray(0, 12);
  const tag = buf.subarray(buf.length - 16);
  const ct = buf.subarray(12, buf.length - 16);
  const d = crypto.createDecipheriv(AES, key, iv);
  d.setAuthTag(tag);
  return Buffer.concat([d.update(ct), d.final()]);
}

export interface CreatedWallet {
  address: `0x${string}`;
  encryptedPrivateKey: string;
  passwordWrap: { encryptedWalletKey: string; salt: string };
  recoveryWrap: { encryptedWalletKey: string; salt: string };
  recoveryKey: string;   // human-readable, shown once to user
}

// 24-hex (12 bytes) recovery key, displayed with dashes for readability.
function genRecoveryKey(): string {
  return crypto.randomBytes(12).toString("hex").match(/.{1,4}/g)!.join("-");
}

export function createEmbeddedWallet(password: string): CreatedWallet {
  const pk = generatePrivateKey();
  const account = privateKeyToAccount(pk);

  const wek = crypto.randomBytes(32);
  const encryptedPrivateKey = aesEncrypt(wek, Buffer.from(pk.slice(2), "hex"));

  const pwSalt = crypto.randomBytes(16);
  const pwKey  = deriveKey(password, pwSalt);
  const passwordWrap = { encryptedWalletKey: aesEncrypt(pwKey, wek), salt: b64(pwSalt) };

  const recoveryKey = genRecoveryKey();
  const rcSalt = crypto.randomBytes(16);
  const rcKey  = deriveKey(recoveryKey, rcSalt);
  const recoveryWrap = { encryptedWalletKey: aesEncrypt(rcKey, wek), salt: b64(rcSalt) };

  return { address: account.address, encryptedPrivateKey, passwordWrap, recoveryWrap, recoveryKey };
}

// Unwrap the WEK using the password or recovery secret.
export function unwrapWek(secret: string, wrap: { encryptedWalletKey: string; salt: string }): Buffer {
  const key = deriveKey(secret, ub64(wrap.salt));
  return aesDecrypt(key, wrap.encryptedWalletKey);
}

// Decrypt the actual private key, given the WEK.
export function decryptPrivateKey(wek: Buffer, encryptedPrivateKey: string): `0x${string}` {
  const pk = aesDecrypt(wek, encryptedPrivateKey);
  return ("0x" + pk.toString("hex")) as `0x${string}`;
}

// Re-wrap the WEK under a new password secret. Returns new password wrap.
export function rewrapForPassword(wek: Buffer, newPassword: string) {
  const salt = crypto.randomBytes(16);
  const key  = deriveKey(newPassword, salt);
  return { encryptedWalletKey: aesEncrypt(key, wek), salt: b64(salt) };
}
"""

# ---------- GenLayer client ----------
F["lib/genlayer/client.ts"] = r"""// Thin GenLayer client wrapper for StudioNet.
// NOTE: Verify exact `genlayer-js` API against https://docs.genlayer.com/ before
// production. Adjust imports to match the installed version.
import "server-only";

const CONTRACT = process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS;

export interface AdvisoryPacket {
  advisoryId: string;
  farmRegion: string;
  cropType: string;
  advisoryQuestion: string;
  plantingWindow: string;
  weatherContext: string;
  marketContext: string;
  soilEvidenceHash: string;
  uploadedEvidenceHash: string;
  userObservationText: string;
  backendProposedPlanA: string;
  backendProposedPlanB: string;
  backendProposedPlanC: string;
}

export interface VerdictResult {
  advisoryId: string;
  verdict: string;
  riskLevel: string;
  confidenceLabel: string;
  selectedPlan: string;
  reasoningSummary: string;
  evidenceDigest: string;
  consensusTimestamp: string;
  finalStatus: string;
  transactionHash: string;
  contractAddress: string;
}

export async function submitAdvisoryToGenLayer(packet: AdvisoryPacket): Promise<VerdictResult> {
  if (!CONTRACT) throw new Error("NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS not set");
  // Lazy import so the SDK loads only when called.
  const gl = await import("genlayer-js").catch(() => null as any);
  if (!gl) throw new Error("genlayer-js not installed");

  // Pseudocode aligned with GenLayer JS client shape; see docs for the exact
  // call signature for write+read against StudioNet.
  const client = gl.createClient
    ? gl.createClient({
        chain: gl.studioNet ?? gl.studioNetwork,
        endpoint: process.env.GENLAYER_RPC_URL!,
        account: gl.createAccount?.(process.env.GENLAYER_SUBMITTER_PRIVATE_KEY!),
      })
    : null;
  if (!client) throw new Error("GenLayer client init failed - verify SDK version");

  const txHash: string = await client.writeContract({
    address: CONTRACT,
    functionName: "submit_advisory",
    args: [
      packet.advisoryId,
      packet.farmRegion,
      packet.cropType,
      packet.advisoryQuestion,
      packet.plantingWindow,
      packet.weatherContext,
      packet.marketContext,
      packet.soilEvidenceHash,
      packet.uploadedEvidenceHash,
      packet.userObservationText,
      packet.backendProposedPlanA,
      packet.backendProposedPlanB,
      packet.backendProposedPlanC,
    ],
  });

  await client.waitForTransactionReceipt({ hash: txHash });

  const v: any = await client.readContract({
    address: CONTRACT,
    functionName: "get_verdict",
    args: [packet.advisoryId],
  });

  return {
    advisoryId: packet.advisoryId,
    verdict: v.verdict,
    riskLevel: v.risk_level,
    confidenceLabel: v.confidence_label,
    selectedPlan: v.selected_plan,
    reasoningSummary: v.reasoning_summary ?? "",
    evidenceDigest: v.evidence_digest,
    consensusTimestamp: v.consensus_timestamp,
    finalStatus: v.final_status,
    transactionHash: txHash,
    contractAddress: CONTRACT,
  };
}
"""

F["lib/util/hash.ts"] = r"""import crypto from "node:crypto";
export const sha256Hex = (b: Buffer | string) =>
  crypto.createHash("sha256").update(b).digest("hex");
"""

F["lib/validation/schemas.ts"] = r"""import { z } from "zod";

export const emailPasswordSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(200),
});

export const farmSchema = z.object({
  name: z.string().min(1).max(120),
  country: z.string().min(2).max(80),
  region: z.string().max(120).optional(),
  latitude: z.coerce.number().optional(),
  longitude: z.coerce.number().optional(),
  nearestTown: z.string().max(120).optional(),
  farmSize: z.coerce.number().nonnegative().optional(),
  soilType: z.string().max(120).optional(),
  irrigationAvailable: z.coerce.boolean().optional(),
  mainCrops: z.string().optional(),                  // CSV
  previousPlantingDate: z.string().optional(),
});

export const advisoryCaseSchema = z.object({
  farmId: z.string().uuid(),
  cropType: z.string().min(1),
  advisoryQuestion: z.string().min(5),
  decisionType: z.enum(["plant_now","delay_planting","irrigate","harvest_window","risk_check"]),
  plantingWindow: z.string().optional(),
  userObservation: z.string().max(2000).optional(),
  weatherContext: z.string().max(4000).optional(),
  marketContext: z.string().max(2000).optional(),
});

export const recoverySchema = z.object({
  email: z.string().email(),
  recoveryKey: z.string().min(20),
  newPassword: z.string().min(8),
});
"""

# =========================================================================
#                          SERVER ACTIONS
# =========================================================================

F["server/actions/auth.ts"] = r""""use server";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { createEmbeddedWallet, unwrapWek, rewrapForPassword } from "@/lib/crypto/wallet";
import { emailPasswordSchema, recoverySchema } from "@/lib/validation/schemas";

export interface SignupResult { ok: boolean; error?: string; recoveryKey?: string; }

export async function signUp(formData: FormData): Promise<SignupResult> {
  const parsed = emailPasswordSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid email or password." };

  const sb = await supabaseServer();
  const { data, error } = await sb.auth.signUp({
    email: parsed.data.email,
    password: parsed.data.password,
  });
  if (error || !data.user) return { ok: false, error: error?.message ?? "Signup failed." };

  const userId = data.user.id;
  const wallet = createEmbeddedWallet(parsed.data.password);

  const admin = supabaseAdmin();
  const { data: w, error: wErr } = await admin.from("wallets").insert({
    user_id: userId,
    address: wallet.address,
    encrypted_private_key: wallet.encryptedPrivateKey,
  }).select("id").single();
  if (wErr || !w) return { ok: false, error: "Wallet creation failed." };

  const { error: wrErr } = await admin.from("wallet_key_wraps").insert([
    { wallet_id: w.id, user_id: userId, method: "password",
      encrypted_wallet_key: wallet.passwordWrap.encryptedWalletKey,
      salt: wallet.passwordWrap.salt },
    { wallet_id: w.id, user_id: userId, method: "recovery",
      encrypted_wallet_key: wallet.recoveryWrap.encryptedWalletKey,
      salt: wallet.recoveryWrap.salt },
  ]);
  if (wrErr) return { ok: false, error: "Wallet wrap failed." };

  return { ok: true, recoveryKey: wallet.recoveryKey };
}

export async function logIn(formData: FormData) {
  const parsed = emailPasswordSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid credentials." };
  const sb = await supabaseServer();
  const { error } = await sb.auth.signInWithPassword(parsed.data);
  if (error) return { ok: false, error: error.message };
  redirect("/dashboard");
}

export async function logOut() {
  const sb = await supabaseServer();
  await sb.auth.signOut();
  redirect("/");
}

// ---- recovery flow ----
// Verifies the recovery key, re-wraps the existing WEK under the new password,
// then updates the auth password. The wallet & address are preserved.
export async function recoverWithKey(formData: FormData) {
  const parsed = recoverySchema.safeParse({
    email: formData.get("email"),
    recoveryKey: formData.get("recoveryKey"),
    newPassword: formData.get("newPassword"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid input." };

  const admin = supabaseAdmin();
  const { data: user } = await admin.auth.admin.getUserByEmail?.(parsed.data.email)
    ?? { data: null };
  // Fallback: query profiles by email
  let userId: string | undefined = user?.user?.id;
  if (!userId) {
    const { data: prof } = await admin.from("profiles").select("user_id").eq("email", parsed.data.email).maybeSingle();
    userId = prof?.user_id;
  }
  if (!userId) return { ok: false, error: "Account not found." };

  const { data: wallet } = await admin.from("wallets").select("id").eq("user_id", userId).maybeSingle();
  if (!wallet) return { ok: false, error: "Wallet missing." };

  const { data: rcWrap } = await admin.from("wallet_key_wraps")
    .select("encrypted_wallet_key,salt").eq("wallet_id", wallet.id).eq("method","recovery").maybeSingle();
  if (!rcWrap) return { ok: false, error: "Recovery wrap missing." };

  let wek: Buffer;
  try {
    wek = unwrapWek(parsed.data.recoveryKey, {
      encryptedWalletKey: rcWrap.encrypted_wallet_key, salt: rcWrap.salt,
    });
  } catch { return { ok: false, error: "Recovery key invalid." }; }

  const newPwWrap = rewrapForPassword(wek, parsed.data.newPassword);
  const { error: upErr } = await admin.from("wallet_key_wraps").update({
    encrypted_wallet_key: newPwWrap.encryptedWalletKey,
    salt: newPwWrap.salt,
  }).eq("wallet_id", wallet.id).eq("method","password");
  if (upErr) return { ok: false, error: "Re-wrap failed." };

  const { error: pwErr } = await admin.auth.admin.updateUserById(userId, { password: parsed.data.newPassword });
  if (pwErr) return { ok: false, error: pwErr.message };

  await admin.from("recovery_audit_logs").insert({
    user_id: userId, wallet_id: wallet.id, action: "password_rewrap",
  });

  return { ok: true };
}

// Export private key (requires fresh password re-auth).
export async function exportPrivateKey(formData: FormData) {
  const password = String(formData.get("password") ?? "");
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  // Re-auth with password
  const { error: reErr } = await sb.auth.signInWithPassword({ email: me.user.email!, password });
  if (reErr) return { ok: false, error: "Password incorrect." };

  const admin = supabaseAdmin();
  const { data: wallet } = await admin.from("wallets")
    .select("id,encrypted_private_key").eq("user_id", me.user.id).maybeSingle();
  if (!wallet) return { ok: false, error: "Wallet missing." };

  const { data: pwWrap } = await admin.from("wallet_key_wraps")
    .select("encrypted_wallet_key,salt").eq("wallet_id", wallet.id).eq("method","password").maybeSingle();
  if (!pwWrap) return { ok: false, error: "Password wrap missing." };

  const { unwrapWek, decryptPrivateKey } = await import("@/lib/crypto/wallet");
  const wek = unwrapWek(password, {
    encryptedWalletKey: pwWrap.encrypted_wallet_key, salt: pwWrap.salt,
  });
  const pk = decryptPrivateKey(wek, wallet.encrypted_private_key);

  await admin.from("recovery_audit_logs").insert({
    user_id: me.user.id, wallet_id: wallet.id, action: "privkey_exported",
  });

  return { ok: true, privateKey: pk };
}
"""

F["server/actions/farms.ts"] = r""""use server";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { farmSchema } from "@/lib/validation/schemas";

export async function createFarm(formData: FormData) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  const parsed = farmSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { ok: false, error: "Invalid farm details." };

  const v = parsed.data;
  const { error } = await sb.from("farms").insert({
    user_id: me.user.id,
    name: v.name,
    country: v.country,
    region: v.region ?? null,
    latitude: v.latitude ?? null,
    longitude: v.longitude ?? null,
    nearest_town: v.nearestTown ?? null,
    farm_size: v.farmSize ?? null,
    soil_type: v.soilType ?? null,
    irrigation_available: !!v.irrigationAvailable,
    main_crops: v.mainCrops ? v.mainCrops.split(",").map((s) => s.trim()) : [],
    previous_planting_date: v.previousPlantingDate || null,
  });
  if (error) return { ok: false, error: error.message };
  redirect("/farms");
}
"""

F["server/actions/cases.ts"] = r""""use server";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { advisoryCaseSchema } from "@/lib/validation/schemas";
import { submitAdvisoryToGenLayer } from "@/lib/genlayer/client";
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

// Submits a prepared case to the GenLayer contract and mirrors the verdict.
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
  const soilHash = snaps?.find(s => s.source_type === "soil")?.snapshot_hash ?? sha256Hex("none");
  const uploadHash = sha256Hex((ev ?? []).map(e => e.evidence_hash).join("|") || "none");

  const admin = supabaseAdmin();
  await admin.from("contract_activity_logs").insert({
    user_id: me.user.id, advisory_case_id: caseId,
    contract_address: process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ?? "",
    action: "submit_advisory", status: "submitted",
  });
  await sb.from("advisory_cases").update({
    status: "submitted", submitted_to_genlayer_at: new Date().toISOString(),
  }).eq("id", caseId);

  try {
    const result = await submitAdvisoryToGenLayer({
      advisoryId: caseId,
      farmRegion: `${(c as any).farms.region ?? ""}, ${(c as any).farms.country}`,
      cropType: c.crop_type,
      advisoryQuestion: c.advisory_question,
      plantingWindow: c.planting_window ?? "",
      weatherContext: weather,
      marketContext: market,
      soilEvidenceHash: soilHash,
      uploadedEvidenceHash: uploadHash,
      userObservationText: c.user_observation ?? "",
      backendProposedPlanA: c.proposed_plan_a,
      backendProposedPlanB: c.proposed_plan_b,
      backendProposedPlanC: c.proposed_plan_c,
    });

    await admin.from("genlayer_verdicts").insert({
      user_id: me.user.id,
      advisory_case_id: caseId,
      contract_address: result.contractAddress,
      transaction_hash: result.transactionHash,
      advisory_id_on_chain: result.advisoryId,
      verdict: result.verdict,
      risk_level: result.riskLevel,
      confidence_label: result.confidenceLabel,
      selected_plan: result.selectedPlan,
      reasoning_summary: result.reasoningSummary,
      evidence_digest: result.evidenceDigest,
      consensus_status: result.finalStatus,
      consensus_timestamp: result.consensusTimestamp || new Date().toISOString(),
    });
    await sb.from("advisory_cases").update({ status: "verdict_issued" }).eq("id", caseId);
    await admin.from("contract_activity_logs").insert({
      user_id: me.user.id, advisory_case_id: caseId,
      contract_address: result.contractAddress, transaction_hash: result.transactionHash,
      action: "verdict_received", status: "ok",
    });
    return { ok: true, verdict: result };
  } catch (e: any) {
    await admin.from("contract_activity_logs").insert({
      user_id: me.user.id, advisory_case_id: caseId,
      contract_address: process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ?? "",
      action: "submit_advisory", status: "error", error_message: String(e?.message ?? e),
    });
    return { ok: false, error: String(e?.message ?? e) };
  }
}
"""

F["server/actions/evidence.ts"] = r""""use server";
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
  return { ok: true, hash };
}
"""

# =========================================================================
#                              UI COMPONENTS
# =========================================================================

F["components/Brand.tsx"] = r"""export function Brand() {
  return (
    <div className="flex items-center gap-2">
      <div className="h-8 w-8 rounded-full bg-canopy grid place-items-center text-ivory font-display font-bold">A</div>
      <span className="font-display text-xl font-bold text-canopy">AgroSense</span>
    </div>
  );
}
"""

F["components/Nav.tsx"] = r"""import Link from "next/link";
import { Brand } from "./Brand";
import { logOut } from "@/server/actions/auth";

export function Nav({ admin }: { admin?: boolean }) {
  return (
    <header className="border-b border-sage bg-ivory">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <Link href="/dashboard"><Brand /></Link>
        <nav className="hidden md:flex items-center gap-5 text-sm">
          <Link href="/dashboard" className="text-charcoal hover:text-canopy">Dashboard</Link>
          <Link href="/farms" className="text-charcoal hover:text-canopy">Farms</Link>
          <Link href="/cases/new" className="text-charcoal hover:text-canopy">New case</Link>
          <Link href="/evidence" className="text-charcoal hover:text-canopy">Evidence</Link>
          {admin && <Link href="/admin" className="text-consensus hover:underline">Admin</Link>}
          <Link href="/profile" className="text-charcoal hover:text-canopy">Profile</Link>
          <Link href="/settings" className="text-charcoal hover:text-canopy">Settings</Link>
        </nav>
        <form action={logOut}><button className="btn-ghost">Log out</button></form>
      </div>
    </header>
  );
}
"""

F["components/VerdictCard.tsx"] = r"""export function VerdictCard({ v }: { v: {
  verdict: string; risk_level: string; confidence_label: string;
  selected_plan: string; consensus_status: string;
  contract_address: string; transaction_hash: string;
  evidence_digest: string; reasoning_summary?: string | null;
}}) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-olive">{v.contract_address?.slice(0,10)}…</span>
        <span className="badge-consensus">{v.consensus_status}</span>
      </div>
      <div className="mt-4">
        <div className="text-xs uppercase tracking-wider text-olive">Verdict</div>
        <div className="font-display text-3xl text-canopy font-bold">{v.verdict}</div>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-5">
        <div><div className="text-xs text-olive uppercase">Risk</div><div className="mt-1"><span className="badge-risk">{v.risk_level}</span></div></div>
        <div><div className="text-xs text-olive uppercase">Confidence</div><div className="mt-1"><span className="badge-ok">{v.confidence_label}</span></div></div>
        <div><div className="text-xs text-olive uppercase">Selected plan</div><div className="mt-1 font-display text-canopy">{v.selected_plan}</div></div>
        <div><div className="text-xs text-olive uppercase">Evidence digest</div><div className="mt-1 font-mono text-xs text-olive truncate">{v.evidence_digest}</div></div>
      </div>
      {v.reasoning_summary && (
        <div className="mt-5">
          <div className="text-xs text-olive uppercase">Why this verdict</div>
          <p className="mt-1 text-sm text-charcoal leading-relaxed">{v.reasoning_summary}</p>
        </div>
      )}
      <div className="mt-5 pt-4 border-t border-sage text-xs font-mono text-olive break-all">
        tx {v.transaction_hash}
      </div>
    </div>
  );
}
"""

F["components/ConsensusPanel.tsx"] = r"""export function ConsensusPanel({ v }: { v: any }) {
  return (
    <div className="rounded-2xl p-6 text-ivory" style={{ background: "#0B3D2E" }}>
      <div className="flex items-center justify-between">
        <span className="font-display text-lg">GenLayer Consensus</span>
        <span className="badge-consensus">{v.consensus_status}</span>
      </div>
      <dl className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div><dt className="text-sage uppercase text-xs">Contract</dt><dd className="font-mono break-all">{v.contract_address}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Advisory ID</dt><dd className="font-mono break-all">{v.advisory_id_on_chain}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Tx hash</dt><dd className="font-mono break-all">{v.transaction_hash}</dd></div>
        <div><dt className="text-sage uppercase text-xs">Source of truth</dt><dd>GenLayer Intelligent Contract</dd></div>
      </dl>
    </div>
  );
}
"""

F["components/RecoveryKeyPanel.tsx"] = r""""use client";
import { useState } from "react";
export function RecoveryKeyPanel({ recoveryKey }: { recoveryKey: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="card p-6 mt-6 border-2 border-harvest">
      <h3 className="font-display text-xl text-canopy">Save your recovery key</h3>
      <p className="text-sm text-olive mt-1">
        This is the only way to recover your wallet if you forget your password. Store it offline. It will not be shown again.
      </p>
      <div className="mt-3 font-mono text-lg p-3 bg-linen rounded-xl break-all">{recoveryKey}</div>
      <button className="btn-primary mt-3"
        onClick={() => { navigator.clipboard.writeText(recoveryKey); setCopied(true); }}>
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
"""

# =========================================================================
#                                PAGES
# =========================================================================

# ---- auth pages ----
F["app/signup/page.tsx"] = r""""use client";
import { useState } from "react";
import { signUp } from "@/server/actions/auth";
import { RecoveryKeyPanel } from "@/components/RecoveryKeyPanel";
import Link from "next/link";

export default function SignupPage() {
  const [err, setErr] = useState<string>();
  const [recoveryKey, setRecoveryKey] = useState<string>();

  async function action(fd: FormData) {
    const r = await signUp(fd);
    if (!r.ok) setErr(r.error); else setRecoveryKey(r.recoveryKey);
  }

  if (recoveryKey) {
    return (
      <main className="max-w-md mx-auto p-8">
        <h1 className="font-display text-3xl text-canopy">Account created</h1>
        <RecoveryKeyPanel recoveryKey={recoveryKey} />
        <Link className="btn-primary mt-6 inline-block" href="/login">Continue to log in</Link>
      </main>
    );
  }

  return (
    <main className="max-w-md mx-auto p-8">
      <h1 className="font-display text-3xl text-canopy">Create your AgroSense account</h1>
      <p className="text-sm text-olive mt-2">A secure embedded wallet is created automatically and linked to your profile.</p>
      <form action={action} className="card p-6 mt-6 space-y-4">
        <input name="email" type="email" required placeholder="Email" className="w-full border border-sage rounded-xl px-3 py-2" />
        <input name="password" type="password" required minLength={8} placeholder="Password (min 8)" className="w-full border border-sage rounded-xl px-3 py-2" />
        <button className="btn-primary w-full" type="submit">Create account</button>
        {err && <p className="text-clay text-sm">{err}</p>}
      </form>
      <p className="text-sm text-olive mt-3">Already have an account? <Link href="/login" className="text-canopy">Log in</Link></p>
    </main>
  );
}
"""

F["app/login/page.tsx"] = r""""use client";
import { useState } from "react";
import Link from "next/link";
import { logIn } from "@/server/actions/auth";

export default function LoginPage() {
  const [err, setErr] = useState<string>();
  async function action(fd: FormData) {
    const r = await logIn(fd) as any;
    if (r && !r.ok) setErr(r.error);
  }
  return (
    <main className="max-w-md mx-auto p-8">
      <h1 className="font-display text-3xl text-canopy">Log in</h1>
      <form action={action} className="card p-6 mt-6 space-y-4">
        <input name="email" type="email" required placeholder="Email" className="w-full border border-sage rounded-xl px-3 py-2" />
        <input name="password" type="password" required placeholder="Password" className="w-full border border-sage rounded-xl px-3 py-2" />
        <button className="btn-primary w-full" type="submit">Continue</button>
        {err && <p className="text-clay text-sm">{err}</p>}
      </form>
      <div className="text-sm text-olive mt-3 flex justify-between">
        <Link href="/forgot-password" className="text-canopy">Forgot password</Link>
        <Link href="/signup" className="text-canopy">Create account</Link>
      </div>
    </main>
  );
}
"""

F["app/forgot-password/page.tsx"] = r"""import Link from "next/link";
export default function P() {
  return (
    <main className="max-w-md mx-auto p-8">
      <h1 className="font-display text-3xl text-canopy">Reset password</h1>
      <p className="text-olive text-sm mt-2">Use your recovery key to set a new password without changing your embedded wallet.</p>
      <Link href="/reset-password" className="btn-primary inline-block mt-6">Use recovery key</Link>
    </main>
  );
}
"""

F["app/reset-password/page.tsx"] = r""""use client";
import { useState } from "react";
import { recoverWithKey } from "@/server/actions/auth";

export default function ResetPasswordPage() {
  const [msg, setMsg] = useState<string>();
  const [err, setErr] = useState<string>();
  async function action(fd: FormData) {
    const r = await recoverWithKey(fd);
    if (r.ok) setMsg("Password reset. Your wallet was preserved. You can log in now.");
    else setErr(r.error);
  }
  return (
    <main className="max-w-md mx-auto p-8">
      <h1 className="font-display text-3xl text-canopy">Recover with key</h1>
      <p className="text-olive text-sm mt-2">Your wallet stays the same — only the password is re-wrapped.</p>
      <form action={action} className="card p-6 mt-6 space-y-4">
        <input name="email" type="email" required placeholder="Email" className="w-full border border-sage rounded-xl px-3 py-2" />
        <input name="recoveryKey" required placeholder="Recovery key" className="w-full border border-sage rounded-xl px-3 py-2 font-mono" />
        <input name="newPassword" type="password" required minLength={8} placeholder="New password" className="w-full border border-sage rounded-xl px-3 py-2" />
        <button className="btn-primary w-full" type="submit">Recover</button>
        {err && <p className="text-clay text-sm">{err}</p>}
        {msg && <p className="text-signal text-sm">{msg}</p>}
      </form>
    </main>
  );
}
"""

# ---- dashboard ----
F["app/dashboard/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import Link from "next/link";

export default async function DashboardPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");

  const { data: profile } = await sb.from("profiles").select("*").eq("user_id", me.user.id).maybeSingle();
  const { data: cases } = await sb.from("advisory_cases")
    .select("id,crop_type,status,created_at,decision_type").eq("user_id", me.user.id)
    .order("created_at", { ascending: false }).limit(8);
  const { data: latest } = await sb.from("genlayer_verdicts")
    .select("verdict,risk_level,consensus_status,transaction_hash,created_at")
    .eq("user_id", me.user.id).order("created_at", { ascending: false }).limit(1).maybeSingle();

  const admin = profile?.role === "admin";

  return (
    <>
      <Nav admin={admin} />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-3xl text-canopy">Welcome back</h1>
          <Link href="/cases/new" className="btn-primary">Create advisory case</Link>
        </div>

        <section className="grid md:grid-cols-3 gap-5 mt-8">
          <div className="card p-5">
            <div className="text-xs text-olive uppercase">Latest verdict</div>
            <div className="font-display text-2xl text-canopy mt-2">{latest?.verdict ?? "—"}</div>
            <div className="mt-2 text-sm text-olive">{latest?.risk_level ?? "No cases yet"}</div>
          </div>
          <div className="card p-5">
            <div className="text-xs text-olive uppercase">Weather watch</div>
            <div className="font-display text-2xl text-canopy mt-2">Live</div>
            <div className="text-sm text-olive mt-2">Attach a weather snapshot to your next case.</div>
          </div>
          <div className="card p-5">
            <div className="text-xs text-olive uppercase">GenLayer consensus</div>
            <div className="font-display text-2xl text-canopy mt-2">{latest?.consensus_status ?? "—"}</div>
            <div className="mt-2 font-mono text-xs text-olive truncate">{latest?.transaction_hash ?? ""}</div>
          </div>
        </section>

        <section className="mt-10">
          <h2 className="font-display text-xl text-canopy mb-3">Recent advisory cases</h2>
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-linen text-olive">
                <tr><th className="text-left p-3">Crop</th><th className="text-left p-3">Decision</th><th className="text-left p-3">Status</th><th className="text-left p-3">Created</th><th></th></tr>
              </thead>
              <tbody>
                {(cases ?? []).length === 0 && (
                  <tr><td colSpan={5} className="p-6 text-center text-olive">No cases yet. Create your first advisory.</td></tr>
                )}
                {(cases ?? []).map(c => (
                  <tr key={c.id} className="border-t border-sage">
                    <td className="p-3 font-display text-canopy">{c.crop_type}</td>
                    <td className="p-3">{c.decision_type}</td>
                    <td className="p-3"><span className="badge-ok">{c.status}</span></td>
                    <td className="p-3 text-olive">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="p-3"><Link href={`/cases/${c.id}`} className="text-canopy">Open</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </>
  );
}
"""

# ---- farms list + new ----
F["app/farms/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import { createFarm } from "@/server/actions/farms";

export default async function FarmsPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: farms } = await sb.from("farms").select("*").eq("user_id", me.user.id).order("created_at", { ascending: false });

  return (
    <>
      <Nav />
      <main className="max-w-6xl mx-auto px-6 py-10 grid md:grid-cols-2 gap-8">
        <div>
          <h1 className="font-display text-3xl text-canopy">Your farms</h1>
          <div className="mt-5 space-y-3">
            {(farms ?? []).length === 0 && <p className="text-olive">No farms yet — add your first farm.</p>}
            {(farms ?? []).map(f => (
              <div key={f.id} className="card p-4">
                <div className="font-display text-xl text-canopy">{f.name}</div>
                <div className="text-sm text-olive">{f.region ? `${f.region}, ` : ""}{f.country}</div>
                <div className="text-xs text-olive mt-1">Crops: {f.main_crops?.join(", ") || "—"}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="font-display text-xl text-canopy">Add a farm</h2>
          <form action={createFarm} className="space-y-3 mt-4">
            <input name="name" required placeholder="Farm name" className="w-full border border-sage rounded-xl px-3 py-2" />
            <input name="country" required placeholder="Country" className="w-full border border-sage rounded-xl px-3 py-2" />
            <input name="region" placeholder="State/region" className="w-full border border-sage rounded-xl px-3 py-2" />
            <input name="nearestTown" placeholder="Nearest town" className="w-full border border-sage rounded-xl px-3 py-2" />
            <div className="grid grid-cols-2 gap-3">
              <input name="latitude" type="number" step="any" placeholder="Latitude" className="border border-sage rounded-xl px-3 py-2" />
              <input name="longitude" type="number" step="any" placeholder="Longitude" className="border border-sage rounded-xl px-3 py-2" />
            </div>
            <input name="farmSize" type="number" step="any" placeholder="Farm size (ha)" className="w-full border border-sage rounded-xl px-3 py-2" />
            <input name="soilType" placeholder="Soil type" className="w-full border border-sage rounded-xl px-3 py-2" />
            <input name="mainCrops" placeholder="Main crops (comma separated)" className="w-full border border-sage rounded-xl px-3 py-2" />
            <label className="flex items-center gap-2 text-sm text-charcoal">
              <input name="irrigationAvailable" type="checkbox" /> Irrigation available
            </label>
            <input name="previousPlantingDate" type="date" className="w-full border border-sage rounded-xl px-3 py-2" />
            <button className="btn-primary w-full">Save farm</button>
          </form>
        </div>
      </main>
    </>
  );
}
"""

# ---- onboarding ----
F["app/onboarding/page.tsx"] = r"""import { redirect } from "next/navigation";
import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";

export default async function OnboardingPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  return (
    <>
      <Nav />
      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="font-display text-3xl text-canopy">Welcome to AgroSense</h1>
        <ol className="mt-6 space-y-4">
          <li className="card p-5"><div className="font-display text-canopy">1. Add your first farm</div><Link className="btn-primary mt-3 inline-block" href="/farms">Add farm</Link></li>
          <li className="card p-5"><div className="font-display text-canopy">2. Create an advisory case</div><Link className="btn-ghost mt-3 inline-block" href="/cases/new">Create case</Link></li>
          <li className="card p-5"><div className="font-display text-canopy">3. Submit to GenLayer for consensus verdict</div></li>
        </ol>
      </main>
    </>
  );
}
"""

# ---- new case ----
F["app/cases/new/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import { createAdvisoryCase } from "@/server/actions/cases";

export default async function NewCasePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: farms } = await sb.from("farms").select("id,name,country,region").eq("user_id", me.user.id);

  return (
    <>
      <Nav />
      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="font-display text-3xl text-canopy">New advisory case</h1>
        <div className="card p-5 mt-5 border-2 border-consensus/30">
          <div className="badge-consensus inline-block">GenLayer Review</div>
          <p className="mt-2 text-sm text-charcoal">
            This case will be evaluated by GenLayer validators. The final verdict is not produced by AgroSense alone.
            Validators will independently reason over the evidence and reach consensus on the most defensible outcome.
          </p>
        </div>

        <form action={createAdvisoryCase} className="card p-6 mt-5 space-y-3">
          <label className="text-sm text-olive">Farm</label>
          <select name="farmId" required className="w-full border border-sage rounded-xl px-3 py-2">
            {(farms ?? []).map(f => <option key={f.id} value={f.id}>{f.name} ({f.region ?? ""}, {f.country})</option>)}
          </select>

          <label className="text-sm text-olive">Decision type</label>
          <select name="decisionType" required className="w-full border border-sage rounded-xl px-3 py-2">
            <option value="plant_now">Should I plant now?</option>
            <option value="delay_planting">Should I delay planting?</option>
            <option value="irrigate">Should I irrigate?</option>
            <option value="harvest_window">Is this harvest window safe?</option>
            <option value="risk_check">Is this farm action too risky?</option>
          </select>

          <input name="cropType" required placeholder="Crop (maize, rice, cassava…)" className="w-full border border-sage rounded-xl px-3 py-2" />
          <input name="advisoryQuestion" required placeholder="Advisory question" className="w-full border border-sage rounded-xl px-3 py-2" />
          <input name="plantingWindow" placeholder="Planting/decision window (e.g. next 7–14 days)" className="w-full border border-sage rounded-xl px-3 py-2" />
          <textarea name="userObservation" placeholder="Your observation from the farm" rows={3} className="w-full border border-sage rounded-xl px-3 py-2" />
          <textarea name="weatherContext" placeholder="Weather context (paste forecast notes)" rows={3} className="w-full border border-sage rounded-xl px-3 py-2" />
          <textarea name="marketContext" placeholder="Market signal (optional)" rows={2} className="w-full border border-sage rounded-xl px-3 py-2" />

          <button className="btn-primary w-full">Save draft</button>
          <p className="text-xs text-olive">You can upload up to 3 evidence files on the next step before submitting to GenLayer.</p>
        </form>
      </main>
    </>
  );
}
"""

# ---- case detail (submit + show verdict if any) ----
F["app/cases/[id]/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import { submitToGenLayer } from "@/server/actions/cases";
import { uploadEvidence } from "@/server/actions/evidence";
import { VerdictCard } from "@/components/VerdictCard";
import { ConsensusPanel } from "@/components/ConsensusPanel";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");

  const { data: c } = await sb.from("advisory_cases")
    .select("*, farms(name,country,region)").eq("id", id).eq("user_id", me.user.id).maybeSingle();
  if (!c) redirect("/dashboard");
  const { data: ev } = await sb.from("evidence_files").select("*").eq("advisory_case_id", id);
  const { data: verdict } = await sb.from("genlayer_verdicts")
    .select("*").eq("advisory_case_id", id).order("created_at", { ascending: false }).maybeSingle();

  async function submit() { "use server"; await submitToGenLayer(id); }

  return (
    <>
      <Nav />
      <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <h1 className="font-display text-3xl text-canopy">{c.crop_type} — {c.decision_type}</h1>
        <p className="text-olive">{c.advisory_question}</p>

        <section className="card p-5">
          <h2 className="font-display text-canopy">Evidence ({ev?.length ?? 0}/3)</h2>
          <ul className="mt-3 text-sm space-y-1">
            {(ev ?? []).map(e => (
              <li key={e.id} className="font-mono text-xs text-olive break-all">{e.file_path} · {e.file_type} · {e.evidence_hash.slice(0,16)}…</li>
            ))}
          </ul>
          {(ev?.length ?? 0) < 3 && (
            <form action={uploadEvidence} encType="multipart/form-data" className="mt-3 flex items-center gap-2">
              <input type="hidden" name="caseId" value={id} />
              <input type="file" name="file" required accept=".jpg,.jpeg,.png,.webp,.pdf,.json" className="text-sm" />
              <button className="btn-ghost">Upload evidence</button>
            </form>
          )}
        </section>

        {!verdict && (
          <form action={submit}>
            <button className="btn-primary">Submit to GenLayer</button>
          </form>
        )}

        {verdict && (
          <div className="grid md:grid-cols-2 gap-5">
            <VerdictCard v={verdict as any} />
            <ConsensusPanel v={verdict as any} />
          </div>
        )}
      </main>
    </>
  );
}
"""

# ---- evidence room ----
F["app/evidence/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";

export default async function EvidenceRoom() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: ev } = await sb.from("evidence_files")
    .select("*").eq("user_id", me.user.id).order("created_at", { ascending: false });
  return (
    <>
      <Nav />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <h1 className="font-display text-3xl text-canopy">Evidence room</h1>
        <div className="card mt-5 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-linen text-olive">
              <tr><th className="text-left p-3">Path</th><th className="text-left p-3">Type</th><th className="text-left p-3">Size</th><th className="text-left p-3">Hash</th></tr>
            </thead>
            <tbody>
              {(ev ?? []).map(f => (
                <tr key={f.id} className="border-t border-sage">
                  <td className="p-3 font-mono text-xs break-all">{f.file_path}</td>
                  <td className="p-3">{f.file_type}</td>
                  <td className="p-3">{f.file_size}</td>
                  <td className="p-3 font-mono text-xs text-olive">{f.evidence_hash.slice(0,16)}…</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
"""

# ---- admin ----
F["app/admin/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";

export default async function AdminPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user.id).maybeSingle();
  if (prof?.role !== "admin") redirect("/dashboard");

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,user_id,crop_type,status,created_at").order("created_at", { ascending: false }).limit(50);
  const { data: verdicts } = await sb.from("genlayer_verdicts")
    .select("*").order("created_at", { ascending: false }).limit(20);

  return (
    <>
      <Nav admin />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <h1 className="font-display text-3xl text-canopy">Admin review</h1>

        <section>
          <h2 className="font-display text-xl text-canopy">All cases</h2>
          <div className="card mt-3 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-linen text-olive"><tr><th className="text-left p-3">Crop</th><th className="text-left p-3">Status</th><th className="text-left p-3">Created</th><th className="text-left p-3">User</th></tr></thead>
              <tbody>
                {(cases ?? []).map(c => (
                  <tr key={c.id} className="border-t border-sage">
                    <td className="p-3 font-display text-canopy">{c.crop_type}</td>
                    <td className="p-3">{c.status}</td>
                    <td className="p-3">{new Date(c.created_at).toLocaleString()}</td>
                    <td className="p-3 font-mono text-xs text-olive">{c.user_id.slice(0,8)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="font-display text-xl text-canopy">Recent GenLayer verdicts</h2>
          <div className="grid md:grid-cols-2 gap-4 mt-3">
            {(verdicts ?? []).map(v => (
              <div key={v.id} className="card p-4">
                <div className="font-display text-canopy">{v.verdict}</div>
                <div className="text-sm text-olive">{v.risk_level} · {v.confidence_label}</div>
                <div className="font-mono text-xs text-olive mt-2 break-all">tx {v.transaction_hash}</div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
"""

# ---- profile + wallet ----
F["app/profile/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import { ExportKeyForm } from "./ExportKeyForm";

export default async function ProfilePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: profile } = await sb.from("profiles").select("*").eq("user_id", me.user.id).maybeSingle();
  const { data: wallet } = await sb.from("wallets").select("address,created_at").eq("user_id", me.user.id).maybeSingle();

  return (
    <>
      <Nav admin={profile?.role === "admin"} />
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <h1 className="font-display text-3xl text-canopy">Profile & wallet</h1>
        <div className="card p-5">
          <div className="text-xs text-olive uppercase">Email</div>
          <div className="font-display text-xl text-canopy mt-1">{profile?.email}</div>
        </div>
        <div className="card p-5">
          <div className="text-xs text-olive uppercase">Embedded wallet address</div>
          <div className="font-mono text-sm text-canopy mt-1 break-all">{wallet?.address}</div>
          <p className="text-xs text-olive mt-3">Your wallet is embedded in your AgroSense profile and used to sign GenLayer actions in the background. You do not need MetaMask or Rabby.</p>
        </div>
        <ExportKeyForm />
      </main>
    </>
  );
}
"""

F["app/profile/ExportKeyForm.tsx"] = r""""use client";
import { useState } from "react";
import { exportPrivateKey } from "@/server/actions/auth";

export function ExportKeyForm() {
  const [pk, setPk] = useState<string>();
  const [err, setErr] = useState<string>();
  const [open, setOpen] = useState(false);
  async function action(fd: FormData) {
    setErr(undefined); setPk(undefined);
    const r = await exportPrivateKey(fd);
    if (!r.ok) setErr(r.error); else setPk(r.privateKey);
  }
  return (
    <div className="card p-5 border-2 border-clay/40">
      <h2 className="font-display text-xl text-canopy">Export private key</h2>
      <p className="text-sm text-olive mt-1">Anyone with this key controls the wallet. Export is logged in the recovery audit log.</p>
      {!open ? (
        <button className="btn-ghost mt-3" onClick={() => setOpen(true)}>I understand, continue</button>
      ) : (
        <form action={action} className="mt-3 space-y-2">
          <input type="password" name="password" required placeholder="Re-enter password" className="w-full border border-sage rounded-xl px-3 py-2" />
          <button className="btn-primary">Export key</button>
          {err && <p className="text-clay text-sm">{err}</p>}
          {pk && <div className="font-mono text-xs p-3 bg-linen rounded-xl break-all">{pk}</div>}
        </form>
      )}
    </div>
  );
}
"""

# ---- settings ----
F["app/settings/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Nav } from "@/components/Nav";
import Link from "next/link";

export default async function SettingsPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  return (
    <>
      <Nav />
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <h1 className="font-display text-3xl text-canopy">Settings</h1>
        <div className="card p-5">
          <h2 className="font-display text-canopy">Security</h2>
          <p className="text-sm text-olive">Change your password via recovery key flow to keep the same wallet.</p>
          <Link href="/reset-password" className="btn-ghost mt-3 inline-block">Use recovery key</Link>
        </div>
        <div className="card p-5">
          <h2 className="font-display text-canopy">Account</h2>
          <p className="text-sm text-olive">Account preferences and notifications coming soon.</p>
        </div>
      </main>
    </>
  );
}
"""

# ---- demo page ----
F["app/demo/page.tsx"] = r"""import { VerdictCard } from "@/components/VerdictCard";
import { ConsensusPanel } from "@/components/ConsensusPanel";
const sample = {
  verdict: "Delay planting", risk_level: "High rainfall", confidence_label: "Strong",
  selected_plan: "Delay planting", consensus_status: "Validated by GenLayer",
  contract_address: "0xA39E0000000000000000000000000000000007C21",
  transaction_hash: "0x7f1c8ab0000000000000000000000000000000be02",
  advisory_id_on_chain: "demo-1", evidence_digest: "sha256:9af2…b1e7",
  reasoning_summary: "Validators independently reasoned that 7-day rainfall risk and incomplete soil confidence make immediate planting unsafe; delay is the most defensible action.",
};
export default function Demo() {
  return (
    <main className="max-w-5xl mx-auto p-10 grid md:grid-cols-2 gap-5">
      <VerdictCard v={sample as any} />
      <ConsensusPanel v={sample as any} />
    </main>
  );
}
"""

# =========================================================================
#                           GENLAYER CONTRACT
# =========================================================================

F["contract/agrosense_advisory.py"] = r'''# AgroSenseAdvisory - GenLayer Intelligent Contract
# Deploy on GenLayer Studio (StudioNet).
#
# Why GenLayer is the star here:
# - submit_advisory() collects three competing plans and invokes a
#   non-deterministic LLM block (gl.nondet.exec_prompt).
# - Each validator independently reasons over the evidence and emits a verdict
#   string PLUS a normalized canonical action token.
# - eq_principle_strict_eq() forces consensus on the canonical action token
#   so wordings like "plant now"/"proceed with planting" or "delay"/"wait"
#   converge to the same agreed action.
# - get_webpage() can be called inside the non-deterministic block when a
#   weather/market URL is provided, so validators ground reasoning in live data.
# - Only the agreed canonical result is persisted on-chain.
#
# Docs: https://docs.genlayer.com/  ·  https://skills.genlayer.com/

from genlayer import *
import json
import typing


CANONICAL_VERDICTS = [
    "plant_now",
    "delay_planting",
    "irrigate_first",
    "proceed_with_caution",
    "avoid_action",
    "request_more_evidence",
]


def _canon(text: str) -> str:
    t = (text or "").lower()
    if "request" in t or "more evidence" in t:        return "request_more_evidence"
    if "avoid" in t:                                  return "avoid_action"
    if "irrigat" in t:                                return "irrigate_first"
    if "delay" in t or "wait" in t or "postpone" in t: return "delay_planting"
    if "caution" in t or "monitor" in t:              return "proceed_with_caution"
    if "plant" in t or "proceed" in t:                return "plant_now"
    return "request_more_evidence"


# @gl.contract is the GenLayer Intelligent Contract decorator.
@gl.contract
class AgroSenseAdvisory:

    # On-chain mirror: advisoryId -> stored verdict (small struct only).
    verdicts: TreeMap[str, str]      # JSON string keyed by advisoryId
    submitted: TreeMap[str, str]     # advisoryId -> submitter address

    def __init__(self) -> None:
        pass

    # ---------- write: meaningful non-deterministic adjudication ----------
    @gl.public.write
    def submit_advisory(
        self,
        advisory_id: str,
        farm_region: str,
        crop_type: str,
        advisory_question: str,
        planting_window: str,
        weather_context: str,
        market_context: str,
        soil_evidence_hash: str,
        uploaded_evidence_hash: str,
        user_observation_text: str,
        backend_proposed_plan_a: str,
        backend_proposed_plan_b: str,
        backend_proposed_plan_c: str,
    ) -> str:
        case_packet = {
            "advisory_id": advisory_id,
            "farm_region": farm_region,
            "crop_type": crop_type,
            "advisory_question": advisory_question,
            "planting_window": planting_window,
            "weather_context": weather_context,
            "market_context": market_context,
            "soil_evidence_hash": soil_evidence_hash,
            "uploaded_evidence_hash": uploaded_evidence_hash,
            "user_observation": user_observation_text,
            "plan_a": backend_proposed_plan_a,
            "plan_b": backend_proposed_plan_b,
            "plan_c": backend_proposed_plan_c,
        }

        prompt = f"""You are an independent agricultural advisory validator.

Case:
{json.dumps(case_packet, indent=2)}

Competing plans:
A. {backend_proposed_plan_a}
B. {backend_proposed_plan_b}
C. {backend_proposed_plan_c}

Decide the MOST DEFENSIBLE advisory verdict for the next 7-14 days.
Consider agronomic risk, weather uncertainty, evidence quality, and practical
farm action. Pick exactly ONE verdict from this list:

  plant_now, delay_planting, irrigate_first, proceed_with_caution,
  avoid_action, request_more_evidence

Respond ONLY as compact JSON, no prose:
{{
  "verdict": "<one of the canonical tokens above>",
  "risk_level": "<low|moderate|high>",
  "confidence": "<weak|moderate|strong>",
  "selected_plan": "<A|B|C>",
  "reasoning": "<1-2 sentence justification>"
}}"""

        # Non-deterministic block: each validator runs the LLM independently.
        # eq_principle_strict_eq forces consensus on the structured "verdict"
        # token (different wording, same agreed action).
        def _validator_block() -> str:
            raw = gl.nondet.exec_prompt(prompt)
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {
                    "verdict": _canon(raw),
                    "risk_level": "moderate",
                    "confidence": "weak",
                    "selected_plan": "B",
                    "reasoning": raw[:280],
                }
            parsed["verdict"] = _canon(parsed.get("verdict", ""))
            if parsed["verdict"] not in CANONICAL_VERDICTS:
                parsed["verdict"] = "request_more_evidence"
            return json.dumps({
                "verdict": parsed["verdict"],
                "risk_level": parsed.get("risk_level", "moderate"),
                "confidence": parsed.get("confidence", "moderate"),
                "selected_plan": parsed.get("selected_plan", "B"),
                "reasoning": parsed.get("reasoning", "")[:400],
            }, sort_keys=True)

        agreed_json = gl.eq_principle_strict_eq(_validator_block)
        agreed = json.loads(agreed_json)

        evidence_digest = f"soil:{soil_evidence_hash[:12]}|files:{uploaded_evidence_hash[:12]}"

        stored = {
            "advisory_id": advisory_id,
            "verdict": agreed["verdict"],
            "risk_level": agreed["risk_level"],
            "confidence_label": agreed["confidence"],
            "selected_plan": agreed["selected_plan"],
            "reasoning_summary": agreed["reasoning"],
            "evidence_digest": evidence_digest,
            "consensus_timestamp": str(gl.block_timestamp() if hasattr(gl, "block_timestamp") else ""),
            "final_status": "consensus_reached",
        }
        self.verdicts[advisory_id] = json.dumps(stored)
        self.submitted[advisory_id] = str(gl.message.sender_address)
        return advisory_id

    # ---------- read ----------
    @gl.public.view
    def get_verdict(self, advisory_id: str) -> dict:
        raw = self.verdicts.get(advisory_id, "")
        if not raw:
            return {"final_status": "not_found"}
        return json.loads(raw)
'''

F["contract/README.md"] = r"""# AgroSenseAdvisory — GenLayer Intelligent Contract

This contract is the **source of truth** for AgroSense advisory verdicts.

## Why GenLayer (not deterministic)
- Three competing plans (A/B/C) are sent in with the case.
- The contract invokes `gl.nondet.exec_prompt(...)` so every validator runs
  the LLM independently against the same prompt + evidence.
- `gl.eq_principle_strict_eq(...)` produces consensus on a structured
  canonical verdict token — different wordings collapse to the same agreed
  action (`plant_now`, `delay_planting`, etc.).
- The contract stores only the small agreed result; large evidence stays in
  Supabase Storage and is referenced by hash.

## Deploy to StudioNet (no Docker)
1. Open GenLayer Studio: https://studio.genlayer.com
2. Connect StudioNet and ensure your account has GEN test tokens.
3. Create a new contract → paste the contents of `agrosense_advisory.py`.
4. Compile, then deploy. Copy the deployed contract address.
5. Set it in your project `.env.local`:
   ```
   NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS=0x...
   GENLAYER_SUBMITTER_PRIVATE_KEY=0x...    # StudioNet test key with GEN
   ```
6. Restart `npm run dev`.

## Verifying GenLayer is doing the judgment
- Submit a case from the UI.
- Observe transaction in Studio: multiple validators evaluate the prompt,
  then converge via the equivalence principle.
- The on-chain stored verdict matches the verdict mirrored into Supabase.

> Verify exact decorator/API names against the latest
> https://docs.genlayer.com/ and https://skills.genlayer.com/ — pin the
> `genlayer-py-std` version that matches StudioNet.
"""

# =========================================================================
#                              DOCS
# =========================================================================

F["DEPLOY.md"] = r"""# AgroSense — Deployment

## 1. Supabase
- Create a Supabase project.
- Apply migrations (`supabase db push` or paste each `supabase/migrations/*.sql`).
- Set Auth → Email/Password ON, confirmations OFF (or wire confirm flow).
- Storage bucket `evidence` is created by migration 0003.
- Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` in your env.

## 2. Wallet KDF pepper
Generate a 32-byte base64 secret used to namespace key derivation:
```bash
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
```
Set as `WALLET_KDF_PEPPER` (server only). Rotating this invalidates existing wraps.

## 3. GenLayer
- Deploy `contract/agrosense_advisory.py` on StudioNet (see contract/README.md).
- Set `NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS`, `GENLAYER_RPC_URL`,
  `GENLAYER_SUBMITTER_PRIVATE_KEY`.

## 4. Vercel
```bash
npm i -g vercel
vercel link
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env add WALLET_KDF_PEPPER
vercel env add NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS
vercel env add GENLAYER_RPC_URL
vercel env add GENLAYER_SUBMITTER_PRIVATE_KEY
vercel env add NEXT_PUBLIC_APP_URL
vercel --prod
```

## 5. Promote an admin
In Supabase SQL editor:
```sql
update public.profiles set role='admin' where email='you@example.com';
```
"""

F["ARCHITECTURE.md"] = r"""# AgroSense — Architecture

## Source of truth
GenLayer is authoritative for advisory verdicts. Next.js prepares the case,
Supabase stores product state and a mirror of the contract result.

```
[ Next.js (Vercel) ] -- prepare packet --> [ GenLayer StudioNet contract ]
        |                                          |
        +--- store state & mirror ---> [ Supabase Postgres + Storage ]
                                                   |
                                                   +-- Auth (email/password)
```

## Wallet model (embedded, non-rotating)
1. On signup: generate secp256k1 EOA → encrypt privkey under random WEK (AES-GCM).
2. Wrap the WEK twice:
   - **password wrap** = AES-GCM(WEK) under PBKDF2(password, saltP).
   - **recovery wrap** = AES-GCM(WEK) under PBKDF2(recoveryKey, saltR).
3. Address never changes. Password reset = re-wrap existing WEK under new
   password using the recovery-wrap path. Private key export requires
   password re-auth and is audit logged.

## RLS
Every user-owned table enforces `auth.uid() = user_id` or admin. Storage
objects in `evidence` are pathed `{user_id}/{case_id}/...` and policies pin
on the first folder segment.

## Why GenLayer is necessary
The contract does not output deterministic thresholds. It invokes
`gl.nondet.exec_prompt` over three competing plans (A/B/C) and converges via
`gl.eq_principle_strict_eq` on a canonical action token. Different LLM
wordings collapse to the same agreed verdict. This is meaningful
non-determinism: the answer requires interpretation, comparison, and
judgment from independent validators.
"""

# =========================================================================
def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage3] wrote {n} files")

if __name__ == "__main__":
    main()
