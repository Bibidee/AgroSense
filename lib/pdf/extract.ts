import "server-only";

export async function extractPdfText(buf: Buffer): Promise<string> {
  try {
    const { PDFParse } = await import("pdf-parse");
    // In Vercel serverless, pdfjs falls back to a "fake worker" that dynamically
    // imports workerSrc. The default "./pdf.worker.mjs" is a relative path that
    // doesn't resolve. Point it to the bundled package instead.
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
