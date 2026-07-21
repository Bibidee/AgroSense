import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase/admin";

export const maxDuration = 60;

export async function GET() {
  const log: string[] = [];

  try {
    // 1. Download the known PDF from Supabase storage
    const admin = supabaseAdmin();
    const { data: files } = await admin
      .from("evidence_files")
      .select("id, file_name, file_path, file_bucket, file_type")
      .eq("file_type", "application/pdf")
      .limit(1);

    const f = files?.[0];
    log.push(`file row: ${JSON.stringify(f)}`);

    if (!f?.file_path) {
      return NextResponse.json({ log, error: "no pdf file found" });
    }

    const bucket = f.file_bucket || "evidence";
    const { data: blob, error: dlErr } = await admin.storage
      .from(bucket)
      .download(f.file_path);

    log.push(`download error: ${dlErr?.message ?? "none"}`);
    log.push(`blob type: ${blob?.constructor?.name}`);

    if (!blob) {
      return NextResponse.json({ log, error: "download failed" });
    }

    const buf = Buffer.from(await blob.arrayBuffer());
    log.push(`buf length: ${buf.length}`);
    log.push(`buf[0..3]: ${[...buf.slice(0, 4)].map((b) => b.toString(16)).join(" ")}`);

    // 2. Try pdf-parse (with polyfill)
    if (typeof (globalThis as any).DOMMatrix === "undefined") {
      (globalThis as any).DOMMatrix = class DOMMatrix {
        a = 1; b = 0; c = 0; d = 1; e = 0; f = 0;
        constructor(init?: number[]) {
          if (Array.isArray(init) && init.length === 6) {
            [this.a, this.b, this.c, this.d, this.e, this.f] = init;
          }
        }
        invertSelf() { return this; }
        multiplySelf() { return this; }
        preMultiplySelf() { return this; }
        translate() { return this; }
        scale() { return this; }
        addPath() {}
      };
      log.push("DOMMatrix polyfilled");
    } else {
      log.push("DOMMatrix already defined");
    }
    try {
      const { PDFParse } = await import("pdf-parse");
      log.push("PDFParse imported");
      PDFParse.setWorker("pdfjs-dist/legacy/build/pdf.worker.mjs");
      log.push("worker set");
      const parser = new PDFParse({ data: buf });
      log.push("parser created");
      const result = await parser.getText();
      log.push(`getText done, text length: ${result.text?.length}, pages: ${result.total}`);
      await parser.destroy().catch(() => {});
      return NextResponse.json({ log, text: result.text?.slice(0, 500) });
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      log.push(`pdf-parse error: ${err}`);
      return NextResponse.json({ log, error: err });
    }
  } catch (e: unknown) {
    const err = e instanceof Error ? e.message : String(e);
    log.push(`outer error: ${err}`);
    return NextResponse.json({ log, error: err });
  }
}
