import "server-only";
import { PDFParse } from "pdf-parse";

export async function extractPdfText(buf: Buffer): Promise<string> {
  const parser = new PDFParse({ data: buf });
  try {
    const result = await parser.getText();
    return (result.text ?? "").trim();
  } catch (error) {
    console.error("[extractPdfText]", error);
    return "";
  } finally {
    await parser.destroy().catch(() => undefined);
  }
}
