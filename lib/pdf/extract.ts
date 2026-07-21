import "server-only";

// pdfjs-dist uses DOMMatrix at module level (for canvas rendering — not text extraction).
// Node.js / Vercel serverless doesn't have DOMMatrix; stub it before any pdfjs import.
function ensureDOMMatrix() {
  if (typeof globalThis.DOMMatrix !== "undefined") return;
  // @ts-expect-error — minimal polyfill; real matrix math not needed for text extraction
  globalThis.DOMMatrix = class DOMMatrix {
    a = 1; b = 0; c = 0; d = 1; e = 0; f = 0;
    m11 = 1; m12 = 0; m13 = 0; m14 = 0;
    m21 = 0; m22 = 1; m23 = 0; m24 = 0;
    m31 = 0; m32 = 0; m33 = 1; m34 = 0;
    m41 = 0; m42 = 0; m43 = 0; m44 = 1;
    is2D = true; isIdentity = true;
    constructor(init?: number[] | string) {
      if (Array.isArray(init) && init.length === 6) {
        [this.a, this.b, this.c, this.d, this.e, this.f] = init;
        [this.m11, this.m12, this.m21, this.m22, this.m41, this.m42] = init;
      }
    }
    invertSelf() { return this; }
    multiplySelf() { return this; }
    preMultiplySelf() { return this; }
    translate() { return this; }
    scale() { return this; }
    addPath() {}
  };
}

export async function extractPdfText(buf: Buffer): Promise<string> {
  ensureDOMMatrix();
  try {
    // Pre-import the pdfjs worker with a static string so Next.js/Vercel's
    // file tracer includes it in the function bundle. pdfjs checks
    // globalThis.pdfjsWorker.WorkerMessageHandler first; if set, it skips its
    // own runtime dynamic import (which can't resolve after bundling).
    // @ts-ignore — no types for worker module
    const pdfjsWorker = await import("pdfjs-dist/legacy/build/pdf.worker.mjs");
    // @ts-ignore — pdfjs checks globalThis.pdfjsWorker.WorkerMessageHandler
    globalThis.pdfjsWorker = pdfjsWorker;

    const { PDFParse } = await import("pdf-parse");
    const parser = new PDFParse({ data: buf });
    try {
      const result = await parser.getText();
      return (result.text ?? "").trim();
    } finally {
      await parser.destroy().catch(() => undefined);
    }
  } catch (error) {
    console.error("[extractPdfText]", error);
    return "";
  }
}
