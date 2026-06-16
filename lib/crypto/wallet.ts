// Server-only wallet crypto.
// - Generates secp256k1 keypair (viem).
// - WEK = random 32 bytes. AES-GCM(privkey) keyed by WEK -> wallets.encrypted_private_key
// - Wraps WEK twice (password + recovery) via PBKDF2-SHA256 (210k iter).
import "server-only";
import crypto from "node:crypto";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

const KDF_ITER = 210_000;
const KDF_KEYLEN = 32;
const AES = "aes-256-gcm";

function b64(buf: Buffer | Uint8Array) { return Buffer.from(buf).toString("base64"); }
function ub64(s: string) { return Buffer.from(s, "base64"); }

function pepper(): Buffer {
  const p = process.env.WALLET_KDF_PEPPER || "";
  if (!p) throw new Error("WALLET_KDF_PEPPER not set");
  return Buffer.from(p, "base64");
}

function deriveKey(secret: string, salt: Buffer): Buffer {
  const peppered = Buffer.concat([Buffer.from(secret, "utf8"), pepper()]);
  return crypto.pbkdf2Sync(peppered, salt, KDF_ITER, KDF_KEYLEN, "sha256");
}

function aesEncrypt(key: Buffer, plaintext: Buffer): string {
  const iv = crypto.randomBytes(12);
  const c = crypto.createCipheriv(AES, key, iv);
  const ct = Buffer.concat([c.update(plaintext), c.final()]);
  const tag = c.getAuthTag();
  return b64(Buffer.concat([iv, ct, tag]));
}

function aesDecrypt(key: Buffer, packed: string): Buffer {
  const buf = ub64(packed);
  const iv = buf.subarray(0, 12);
  const tag = buf.subarray(buf.length - 16);
  const ct = buf.subarray(12, buf.length - 16);
  const d = crypto.createDecipheriv(AES, key, iv);
  d.setAuthTag(tag);
  return Buffer.concat([d.update(ct), d.final()]);
}

export interface CreatedWallet {
  address: `0x${string}`;
  encryptedPrivateKey: string;
  passwordWrap: { encryptedWalletKey: string; salt: string };
  recoveryWrap: { encryptedWalletKey: string; salt: string };
  recoveryKey: string;   // human-readable, shown once to user
}

// 24-hex (12 bytes) recovery key, displayed with dashes for readability.
function genRecoveryKey(): string {
  return crypto.randomBytes(12).toString("hex").match(/.{1,4}/g)!.join("-");
}

export function createEmbeddedWallet(password: string): CreatedWallet {
  const pk = generatePrivateKey();
  const account = privateKeyToAccount(pk);

  const wek = crypto.randomBytes(32);
  const encryptedPrivateKey = aesEncrypt(wek, Buffer.from(pk.slice(2), "hex"));

  const pwSalt = crypto.randomBytes(16);
  const pwKey  = deriveKey(password, pwSalt);
  const passwordWrap = { encryptedWalletKey: aesEncrypt(pwKey, wek), salt: b64(pwSalt) };

  const recoveryKey = genRecoveryKey();
  const rcSalt = crypto.randomBytes(16);
  const rcKey  = deriveKey(recoveryKey, rcSalt);
  const recoveryWrap = { encryptedWalletKey: aesEncrypt(rcKey, wek), salt: b64(rcSalt) };

  return { address: account.address, encryptedPrivateKey, passwordWrap, recoveryWrap, recoveryKey };
}

// Unwrap the WEK using the password or recovery secret.
export function unwrapWek(secret: string, wrap: { encryptedWalletKey: string; salt: string }): Buffer {
  const key = deriveKey(secret, ub64(wrap.salt));
  return aesDecrypt(key, wrap.encryptedWalletKey);
}

// Decrypt the actual private key, given the WEK.
export function decryptPrivateKey(wek: Buffer, encryptedPrivateKey: string): `0x${string}` {
  const pk = aesDecrypt(wek, encryptedPrivateKey);
  return ("0x" + pk.toString("hex")) as `0x${string}`;
}

// Re-wrap the WEK under a new password secret. Returns new password wrap.
export function rewrapForPassword(wek: Buffer, newPassword: string) {
  const salt = crypto.randomBytes(16);
  const key  = deriveKey(newPassword, salt);
  return { encryptedWalletKey: aesEncrypt(key, wek), salt: b64(salt) };
}
