import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase/admin";

// Public endpoint — GenLayer validators fetch this during consensus.
// Uses the service-role client so RLS does not block unauthenticated reads.
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ caseId: string }> },
) {
  const { caseId } = await params;
  const admin = supabaseAdmin();

  const { data: files, error } = await admin
    .from("evidence_files")
    .select("file_name, file_type, evidence_hash, extracted_text")
    .eq("advisory_case_id", caseId);

  if (error) {
    return NextResponse.json({ error: "Failed to load evidence." }, { status: 500 });
  }

  const { data: soilSnap } = await admin
    .from("data_snapshots")
    .select("snapshot_json, snapshot_hash")
    .eq("advisory_case_id", caseId)
    .eq("source_type", "soil")
    .maybeSingle();

  const manifest = {
    case_id: caseId,
    soil_evidence: soilSnap
      ? { data: soilSnap.snapshot_json, sha256: soilSnap.snapshot_hash }
      : null,
    documents: (files ?? []).map((f) => ({
      name: f.file_name ?? "unknown",
      mime_type: f.file_type,
      sha256: f.evidence_hash,
      extracted_text: f.extracted_text ?? null,
    })),
  };

  return NextResponse.json(manifest, {
    headers: { "Cache-Control": "no-store" },
  });
}
