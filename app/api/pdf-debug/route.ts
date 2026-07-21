import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase/admin";

export const maxDuration = 60;

export async function GET() {
  const log: string[] = [];

  try {
    const admin = supabaseAdmin();
    const { data: files } = await admin
      .from("evidence_files")
      .select("id, file_name, file_path, file_bucket, file_type")
      .eq("file_type", "application/pdf")
      .limit(1);

    const f = files?.[0];
    log.push(`file: ${JSON.stringify(f)}`);

    if (!f?.file_path) return NextResponse.json({ log, error: "no pdf" });

    const { data: blob, error: dlErr } = await admin.storage
      .from(f.file_bucket || "evidence")
      .download(f.file_path);

    log.push(`dl err: ${dlErr?.message ?? "none"}, buf bytes: ${(await blob?.arrayBuffer())?.byteLength ?? 0}`);
    if (!blob) return NextResponse.json({ log, error: "download failed" });

    const buf = Buffer.from(await blob.arrayBuffer());
    log.push(`buf: ${buf.length} bytes, header: ${[...buf.slice(0, 4)].map(b => b.toString(16)).join(" ")}`);

    // DOMMatrix polyfill
    if (typeof (globalThis as any).DOMMatrix === "undefined") {
      (globalThis as any).DOMMatrix = class DOMMatrix {
        a=1;b=0;c=0;d=1;e=0;f=0;m11=1;m12=0;m21=0;m22=1;m41=0;m42=0;is2D=true;isIdentity=true;
        constructor(init?: number[]) { if (Array.isArray(init) && init.length===6) { [this.a,this.b,this.c,this.d,this.e,this.f]=init; } }
        invertSelf(){return this;} multiplySelf(){return this;} preMultiplySelf(){return this;}
        translate(){return this;} scale(){return this;} addPath(){}
      };
      log.push("DOMMatrix: polyfilled");
    } else {
      log.push("DOMMatrix: already present");
    }

    // Pre-load worker so pdfjs uses globalThis.pdfjsWorker instead of string-import
    try {
      // @ts-ignore — no types for worker module
      const w = await import("pdfjs-dist/legacy/build/pdf.worker.mjs");
      (globalThis as any).pdfjsWorker = w;
      log.push(`worker loaded, keys: ${Object.keys(w).join(",")}`);
    } catch (e: unknown) {
      log.push(`worker load failed: ${e instanceof Error ? e.message : String(e)}`);
    }

    try {
      const { PDFParse } = await import("pdf-parse");
      log.push("PDFParse imported");
      const parser = new PDFParse({ data: buf });
      const result = await parser.getText();
      log.push(`text length: ${result.text?.length}, pages: ${result.total}`);
      await parser.destroy().catch(() => {});
      return NextResponse.json({ log, text: result.text?.slice(0, 500) });
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      log.push(`pdf-parse error: ${err}`);
      return NextResponse.json({ log, error: err });
    }
  } catch (e: unknown) {
    return NextResponse.json({ log, error: e instanceof Error ? e.message : String(e) });
  }
}
