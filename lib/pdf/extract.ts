import "server-only";

export async function extractPdfText(buf: Buffer): Promise<string> {
  try {
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
