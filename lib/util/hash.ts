import crypto from "node:crypto";
export const sha256Hex = (b: Buffer | string) =>
  crypto.createHash("sha256").update(b).digest("hex");
