import "server-only";

// pdfjs-dist worker references DOMMatrix at module level (for canvas rendering).
// In Node.js / Vercel serverless, DOMMatrix is not defined. Polyfill it before
// any import so the worker loads without throwing. Text extraction doesn't use
// DOMMatrix at all — it only appears in the canvas rendering path.
function ensureDOMMatrix() {
  if (typeof globalThis.DOMMatrix !== "undefined") return;
  // @ts-expect-error — minimal polyfill; full spec not needed for text extraction
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
    const { PDFParse } = await import("pdf-parse");
    PDFParse.setWorker("pdfjs-dist/legacy/build/pdf.worker.mjs");
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
