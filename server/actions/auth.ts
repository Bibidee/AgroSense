"use server";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { createEmbeddedWallet, unwrapWek, rewrapForPassword } from "@/lib/crypto/wallet";
import { emailPasswordSchema, recoverySchema } from "@/lib/validation/schemas";

export interface SignupResult { ok: boolean; error?: string; recoveryKey?: string; }

export async function signUp(formData: FormData): Promise<SignupResult> {
  const parsed = emailPasswordSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid email or password." };

  const sb = await supabaseServer();
  const { data, error } = await sb.auth.signUp({
    email: parsed.data.email,
    password: parsed.data.password,
  });
  if (error || !data.user) return { ok: false, error: error?.message ?? "Signup failed." };

  const userId = data.user.id;
  const wallet = createEmbeddedWallet(parsed.data.password);

  const admin = supabaseAdmin();
  const { data: w, error: wErr } = await admin.from("wallets").insert({
    user_id: userId,
    address: wallet.address,
    encrypted_private_key: wallet.encryptedPrivateKey,
  }).select("id").single();
  if (wErr || !w) { console.error("wallet insert", wErr); return { ok: false, error: `Wallet creation failed: ${wErr?.message ?? "unknown"}` }; }

  const { error: wrErr } = await admin.from("wallet_key_wraps").insert([
    { wallet_id: w.id, user_id: userId, method: "password",
      encrypted_wallet_key: wallet.passwordWrap.encryptedWalletKey,
      salt: wallet.passwordWrap.salt },
    { wallet_id: w.id, user_id: userId, method: "recovery",
      encrypted_wallet_key: wallet.recoveryWrap.encryptedWalletKey,
      salt: wallet.recoveryWrap.salt },
  ]);
  if (wrErr) { console.error("wrap insert", wrErr); return { ok: false, error: `Wallet wrap failed: ${wrErr.message}` }; }

  return { ok: true, recoveryKey: wallet.recoveryKey };
}

export async function logIn(formData: FormData) {
  const parsed = emailPasswordSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid credentials." };
  const sb = await supabaseServer();
  const { error } = await sb.auth.signInWithPassword(parsed.data);
  if (error) return { ok: false, error: error.message };
  redirect("/dashboard");
}

export async function logOut() {
  const sb = await supabaseServer();
  await sb.auth.signOut();
  redirect("/");
}

// ---- recovery flow ----
// Verifies the recovery key, re-wraps the existing WEK under the new password,
// then updates the auth password. The wallet & address are preserved.
export async function recoverWithKey(formData: FormData) {
  const parsed = recoverySchema.safeParse({
    email: formData.get("email"),
    recoveryKey: formData.get("recoveryKey"),
    newPassword: formData.get("newPassword"),
  });
  if (!parsed.success) return { ok: false, error: "Invalid input." };

  const admin = supabaseAdmin();
  // Resolve user_id by email via profiles table (auth admin lookup-by-email isn't in SDK v2).
  let userId: string | undefined;
  {
    const { data: prof } = await admin.from("profiles").select("user_id").eq("email", parsed.data.email).maybeSingle();
    userId = prof?.user_id;
  }
  if (!userId) return { ok: false, error: "Account not found." };

  const { data: wallet } = await admin.from("wallets").select("id").eq("user_id", userId).maybeSingle();
  if (!wallet) return { ok: false, error: "Wallet missing." };

  const { data: rcWrap } = await admin.from("wallet_key_wraps")
    .select("encrypted_wallet_key,salt").eq("wallet_id", wallet.id).eq("method","recovery").maybeSingle();
  if (!rcWrap) return { ok: false, error: "Recovery wrap missing." };

  let wek: Buffer;
  try {
    wek = unwrapWek(parsed.data.recoveryKey, {
      encryptedWalletKey: rcWrap.encrypted_wallet_key, salt: rcWrap.salt,
    });
  } catch { return { ok: false, error: "Recovery key invalid." }; }

  const newPwWrap = rewrapForPassword(wek, parsed.data.newPassword);
  const { error: upErr } = await admin.from("wallet_key_wraps").update({
    encrypted_wallet_key: newPwWrap.encryptedWalletKey,
    salt: newPwWrap.salt,
  }).eq("wallet_id", wallet.id).eq("method","password");
  if (upErr) return { ok: false, error: "Re-wrap failed." };

  const { error: pwErr } = await admin.auth.admin.updateUserById(userId, { password: parsed.data.newPassword });
  if (pwErr) return { ok: false, error: pwErr.message };

  await admin.from("recovery_audit_logs").insert({
    user_id: userId, wallet_id: wallet.id, action: "password_rewrap",
  });

  return { ok: true };
}

// Export private key (requires fresh password re-auth).
export async function exportPrivateKey(formData: FormData) {
  const password = String(formData.get("password") ?? "");
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  // Re-auth with password
  const { error: reErr } = await sb.auth.signInWithPassword({ email: me.user.email!, password });
  if (reErr) return { ok: false, error: "Password incorrect." };

  const admin = supabaseAdmin();
  const { data: wallet } = await admin.from("wallets")
    .select("id,encrypted_private_key").eq("user_id", me.user.id).maybeSingle();
  if (!wallet) return { ok: false, error: "Wallet missing." };

  const { data: pwWrap } = await admin.from("wallet_key_wraps")
    .select("encrypted_wallet_key,salt").eq("wallet_id", wallet.id).eq("method","password").maybeSingle();
  if (!pwWrap) return { ok: false, error: "Password wrap missing." };

  const { unwrapWek, decryptPrivateKey } = await import("@/lib/crypto/wallet");
  const wek = unwrapWek(password, {
    encryptedWalletKey: pwWrap.encrypted_wallet_key, salt: pwWrap.salt,
  });
  const pk = decryptPrivateKey(wek, wallet.encrypted_private_key);

  await admin.from("recovery_audit_logs").insert({
    user_id: me.user.id, wallet_id: wallet.id, action: "privkey_exported",
  });

  return { ok: true, privateKey: pk };
}
