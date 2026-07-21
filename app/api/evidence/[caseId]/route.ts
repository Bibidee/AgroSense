import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { extractPdfText } from "@/lib/pdf/extract";

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
    .select("id, file_name, file_type, file_path, file_bucket, evidence_hash, extracted_text")
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

  // Build documents with fallback extraction for PDFs whose extracted_text
  // was blank due to the old broken parser call (pdf-parse v1 API on v2).
  const documents = await Promise.all(
    (files ?? []).map(async (f) => {
      let extractedText = f.extracted_text ?? null;

      if (f.file_type === "application/pdf" && !extractedText && f.file_path) {
        const bucket = f.file_bucket || "evidence";
        const { data: pdf } = await admin.storage.from(bucket).download(f.file_path);

        if (pdf) {
          const buf = Buffer.from(await pdf.arrayBuffer());
          extractedText = await extractPdfText(buf);

          if (extractedText) {
            await admin
              .from("evidence_files")
              .update({ extracted_text: extractedText })
              .eq("id", f.id);
          }
        }
      }

      return {
        name: f.file_name ?? "unknown",
        mime_type: f.file_type,
        sha256: f.evidence_hash,
        extracted_text: extractedText,
      };
    }),
  );

  const manifest = {
    case_id: caseId,
    soil_evidence: soilSnap
      ? { data: soilSnap.snapshot_json, sha256: soilSnap.snapshot_hash }
      : null,
    documents,
  };

  return NextResponse.json(manifest, {
    headers: { "Cache-Control": "no-store" },
  });
}
