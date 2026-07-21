"use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";
import { sha256Hex } from "@/lib/util/hash";

async function extractPdfText(buf: Buffer): Promise<string> {
  try {
    const mod = await import("pdf-parse");
    const pdfParse = (mod as any).default ?? mod;
    const result = await pdfParse(buf);
    return (result.text ?? "").trim();
  } catch {
    return "";
  }
}

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

  const extractedText = file.type === "application/pdf" ? await extractPdfText(buf) : null;

  const { error } = await sb.from("evidence_files").insert({
    user_id: me.user.id,
    advisory_case_id: caseId,
    file_name: file.name,
    file_url: signed?.signedUrl ?? "",
    file_path: path,
    file_bucket: "evidence",
    file_type: file.type,
    file_size: file.size,
    evidence_hash: hash,
    extracted_text: extractedText,
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
