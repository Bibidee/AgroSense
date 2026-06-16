"""
Stage 6 polish: onboarding gate, notifications, data export,
admin replay + export packet, Open-Meteo weather, mobile bottom nav.
Run:  python scripts/stage6_polish.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

# ---------- weather (Open-Meteo, no key) ----------
F["server/actions/weather.ts"] = r""""use server";
// Open-Meteo: https://open-meteo.com/  (no API key needed)
export async function fetchOpenMeteo(lat: number, lon: number) {
  if (Number.isNaN(lat) || Number.isNaN(lon)) {
    return { ok: false, error: "Farm coordinates missing." };
  }
  const url =
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
    `&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max` +
    `&forecast_days=7&timezone=auto`;
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) return { ok: false, error: `Open-Meteo HTTP ${r.status}` };
    const j: any = await r.json();
    const d = j.daily;
    if (!d?.time?.length) return { ok: false, error: "Open-Meteo returned no daily series." };

    const lines = d.time.map((day: string, i: number) => {
      const hi = d.temperature_2m_max[i]; const lo = d.temperature_2m_min[i];
      const mm = d.precipitation_sum[i];  const p  = d.precipitation_probability_max[i];
      return `${day}: ${lo}–${hi}°C · rain ${mm} mm · p ${p}%`;
    });
    const text =
      `7-day forecast (Open-Meteo, ${j.timezone ?? "local"}):\n` +
      lines.join("\n");
    return { ok: true, text, raw: j };
  } catch (e: any) {
    return { ok: false, error: e?.message ?? "Open-Meteo fetch failed" };
  }
}
"""

# ---------- settings actions ----------
F["server/actions/settings.ts"] = r""""use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";

export async function updateNotificationPrefs(prefs: Record<string, boolean>) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const { error } = await sb.from("profiles")
    .update({ notification_prefs: prefs }).eq("user_id", me.user.id);
  if (error) return { ok: false, error: error.message };
  revalidatePath("/settings");
  return { ok: true };
}

// Bundle the user's full data into a JSON blob for download.
export async function exportUserData() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const uid = me.user.id;

  const [
    profileRes, walletRes, farmsRes, casesRes, evidenceRes,
    snapshotsRes, verdictsRes, activityRes, auditRes,
  ] = await Promise.all([
    sb.from("profiles").select("*").eq("user_id", uid).maybeSingle(),
    sb.from("wallets").select("id,address,created_at").eq("user_id", uid).maybeSingle(),
    sb.from("farms").select("*").eq("user_id", uid),
    sb.from("advisory_cases").select("*").eq("user_id", uid),
    sb.from("evidence_files").select("*").eq("user_id", uid),
    sb.from("data_snapshots").select("*").eq("user_id", uid),
    sb.from("genlayer_verdicts").select("*").eq("user_id", uid),
    sb.from("contract_activity_logs").select("*").eq("user_id", uid),
    sb.from("recovery_audit_logs").select("*").eq("user_id", uid),
  ]);

  return {
    ok: true,
    bundle: {
      exported_at: new Date().toISOString(),
      profile: profileRes.data,
      wallet: walletRes.data,
      farms: farmsRes.data ?? [],
      advisory_cases: casesRes.data ?? [],
      evidence_files: evidenceRes.data ?? [],
      data_snapshots: snapshotsRes.data ?? [],
      verdicts: verdictsRes.data ?? [],
      contract_activity: activityRes.data ?? [],
      recovery_audit: auditRes.data ?? [],
    },
  };
}

export async function markOnboardingComplete() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };
  const { error } = await sb.from("profiles")
    .update({ onboarding_completed: true }).eq("user_id", me.user.id);
  if (error) return { ok: false, error: error.message };
  revalidatePath("/dashboard");
  return { ok: true };
}
"""

# ---------- admin actions: replay + export packet ----------
F["server/actions/admin.ts"] = r""""use server";
import { revalidatePath } from "next/cache";
import { supabaseServer } from "@/lib/supabase/server";
import { supabaseAdmin } from "@/lib/supabase/admin";

async function assertAdmin() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." as const };
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user.id).maybeSingle();
  if (prof?.role !== "admin") return { ok: false, error: "Admin only." as const };
  return { ok: true as const, sb, userId: me.user.id };
}

// Replay clears the mirrored verdict and resets case status so the operator can re-submit.
// (Admins can't sign with the user's wallet — re-submission must come from the operator.)
export async function replayCase(caseId: string) {
  const a = await assertAdmin();
  if (!("sb" in a)) return a;
  const admin = supabaseAdmin();
  await admin.from("genlayer_verdicts").delete().eq("advisory_case_id", caseId);
  await a.sb.from("advisory_cases").update({
    status: "ready", submitted_to_genlayer_at: null,
  }).eq("id", caseId);
  await admin.from("contract_activity_logs").insert({
    user_id: a.userId, advisory_case_id: caseId,
    contract_address: process.env.NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS ?? "",
    action: "admin_replay_requested", status: "ok",
  });
  revalidatePath("/admin");
  revalidatePath(`/cases/${caseId}`);
  return { ok: true };
}

// Export the full advisory packet (case + farm + snapshots + evidence) as JSON.
export async function exportAdvisoryPacket(caseId: string) {
  const a = await assertAdmin();
  if (!("sb" in a)) return a;
  const [c, ev, snaps, verdict] = await Promise.all([
    a.sb.from("advisory_cases").select("*, farms(*)").eq("id", caseId).maybeSingle(),
    a.sb.from("evidence_files").select("*").eq("advisory_case_id", caseId),
    a.sb.from("data_snapshots").select("*").eq("advisory_case_id", caseId),
    a.sb.from("genlayer_verdicts").select("*").eq("advisory_case_id", caseId).maybeSingle(),
  ]);
  return {
    ok: true,
    bundle: {
      exported_at: new Date().toISOString(),
      case: c.data,
      evidence: ev.data ?? [],
      snapshots: snaps.data ?? [],
      verdict: verdict.data ?? null,
    },
  };
}
"""

# ---------- Open-Meteo helper button on /cases/new ----------
F["app/cases/new/WeatherPullButton.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { fetchOpenMeteo } from "@/server/actions/weather";

// Auto-fills a textarea by name with Open-Meteo's 7-day summary for the
// currently selected farm. Reads coords from a hidden data attribute on the
// <option> elements so we don't need extra round-trips.
export function WeatherPullButton({ farms }: { farms: { id: string; latitude: number | null; longitude: number | null }[] }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();

  function onClick() {
    setMsg(undefined);
    const sel = document.querySelector<HTMLSelectElement>('select[name="farmId"]');
    const target = document.querySelector<HTMLTextAreaElement>('textarea[name="weatherContext"]');
    if (!sel || !target) { setMsg("Form not ready."); return; }
    const f = farms.find(x => x.id === sel.value);
    if (!f || f.latitude == null || f.longitude == null) {
      setMsg("Selected farm has no coordinates. Add lat/lon in /farms.");
      return;
    }
    start(async () => {
      const r = await fetchOpenMeteo(Number(f.latitude), Number(f.longitude));
      if (!r.ok) { setMsg(r.error || "Fetch failed"); return; }
      target.value = r.text!;
      setMsg("Live forecast filled in.");
    });
  }

  return (
    <div className="flex items-center gap-2">
      <button type="button" onClick={onClick} disabled={pending}
        className="btn-ghost text-xs disabled:opacity-60">
        {pending ? "Fetching…" : "Pull live weather"}
      </button>
      {msg && <span className="text-xs text-sage">{msg}</span>}
    </div>
  );
}
"""

# ---------- Mobile bottom nav ----------
F["components/MobileNav.tsx"] = r""""use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/dashboard", label: "Home",     glyph: "◎" },
  { href: "/cases/new", label: "New",      glyph: "+" },
  { href: "/cases",     label: "Cases",    glyph: "≡" },
  { href: "/evidence",  label: "Evidence", glyph: "▣" },
  { href: "/profile",   label: "Profile",  glyph: "◐" },
];

export function MobileNav() {
  const path = usePathname() ?? "";
  const activeHref = ITEMS
    .filter(n => path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href + "/")))
    .sort((a, b) => b.href.length - a.href.length)[0]?.href;
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-graphite/95 backdrop-blur border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
      <div className="grid grid-cols-5">
        {ITEMS.map(n => {
          const on = activeHref === n.href;
          return (
            <Link key={n.href} href={n.href}
              className={`flex flex-col items-center justify-center py-2.5 text-[10px] uppercase tracking-wider ${on ? "text-biosignal" : "text-sage"}`}>
              <span className={`w-8 h-8 grid place-items-center rounded-lg mb-0.5 ${on ? "bg-biosignal/15 border border-biosignal/30" : "bg-white/5 border border-transparent"}`}>{n.glyph}</span>
              {n.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
"""

# ---------- AppShell: mount MobileNav + onboarding gate ----------
F["components/AppShell.tsx"] = r"""import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { supabaseServer } from "@/lib/supabase/server";
import { CommandRail } from "./CommandRail";
import { TopContextBar } from "./TopContextBar";
import { MobileNav } from "./MobileNav";

export async function AppShell({
  section, subtitle, children,
}: { section: string; subtitle?: string; children: React.ReactNode }) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: profile } = await sb.from("profiles").select("role,email,onboarding_completed").eq("user_id", me.user.id).maybeSingle();
  const { data: wallet } = await sb.from("wallets").select("address").eq("user_id", me.user.id).maybeSingle();

  // Gate: if onboarding not complete and the user isn't already on /onboarding or /farms,
  // funnel them to onboarding. Allow /farms so they can add their first farm.
  const h = await headers();
  const path = h.get("x-pathname") || h.get("next-url") || "";
  const isOnboarding = path.startsWith("/onboarding") || path.startsWith("/farms");
  if (profile && profile.onboarding_completed === false && !isOnboarding) {
    redirect("/onboarding");
  }

  return (
    <div className="min-h-screen bg-field-grid">
      <div className="flex">
        <CommandRail admin={profile?.role === "admin"} email={profile?.email ?? me.user.email} wallet={wallet?.address} />
        <div className="flex-1 min-w-0 pb-20 md:pb-0">
          <TopContextBar section={section} subtitle={subtitle} />
          <main className="px-4 md:px-6 py-6">{children}</main>
        </div>
      </div>
      <MobileNav />
    </div>
  );
}
"""

# ---------- Onboarding stepper (real, gated) ----------
F["app/onboarding/page.tsx"] = r"""import Link from "next/link";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { Brand } from "@/components/Brand";
import { ConsensusBadge } from "@/components/Badges";
import { CompleteOnboardingButton } from "./CompleteOnboardingButton";

export default async function OnboardingPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) redirect("/login");
  const { data: profile } = await sb.from("profiles").select("email,onboarding_completed").eq("user_id", me.user.id).maybeSingle();
  const { data: farms } = await sb.from("farms").select("id").eq("user_id", me.user.id);
  const { data: cases } = await sb.from("advisory_cases").select("id").eq("user_id", me.user.id).limit(1);

  const hasFarm = (farms?.length ?? 0) > 0;
  const hasCase = (cases?.length ?? 0) > 0;
  const stages = [
    { ok: true,       label: "Operator profile created", body: profile?.email, cta: null },
    { ok: true,       label: "Embedded wallet attached", body: "Secured by your password + recovery key.", cta: null },
    { ok: hasFarm,    label: "Add your first farm",      body: "Plot anchors every advisory case.", cta: ["Open farms", "/farms"] as const },
    { ok: hasCase,    label: "Create a sample case",     body: "Submit one advisory packet to engage GenLayer validators.", cta: ["Create case", "/cases/new"] as const },
  ];
  const allDone = stages.every(s => s.ok);

  if (profile?.onboarding_completed) redirect("/dashboard");

  return (
    <div className="min-h-screen bg-field-grid">
      <header className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
        <Brand />
        <ConsensusBadge label="Setup" />
      </header>
      <main className="max-w-5xl mx-auto px-6 pb-20">
        <h1 className="font-display text-4xl text-pearl">Field Intelligence Setup</h1>
        <p className="text-sage mt-3 max-w-xl">Complete the steps below so AgroSense can produce defensible advisory verdicts for your fields.</p>

        <ol className="mt-8 space-y-4">
          {stages.map((s, i) => (
            <li key={i} className={`panel p-5 flex items-start gap-4 ${s.ok ? "border border-biosignal/30" : ""}`}>
              <div className={`w-10 h-10 grid place-items-center rounded-full ${s.ok ? "bg-biosignal/20 text-biosignal" : "bg-white/5 text-sage"} font-display`}>
                {s.ok ? "✓" : String(i + 1).padStart(2, "0")}
              </div>
              <div className="flex-1">
                <div className="font-display text-pearl text-lg">{s.label}</div>
                {s.body && <div className="text-sm text-sage mt-1">{s.body}</div>}
              </div>
              {!s.ok && s.cta && (
                <Link href={s.cta[1]} className="btn-primary text-sm whitespace-nowrap">{s.cta[0]} →</Link>
              )}
            </li>
          ))}
        </ol>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <CompleteOnboardingButton enabled={allDone} />
          {!allDone && <span className="text-sage text-sm">Finish the remaining steps to enter the OS.</span>}
        </div>
      </main>
    </div>
  );
}
"""

F["app/onboarding/CompleteOnboardingButton.tsx"] = r""""use client";
import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { markOnboardingComplete } from "@/server/actions/settings";

export function CompleteOnboardingButton({ enabled }: { enabled: boolean }) {
  const [pending, start] = useTransition();
  const router = useRouter();
  return (
    <button
      disabled={!enabled || pending}
      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      onClick={() => start(async () => {
        const r = await markOnboardingComplete();
        if (r.ok) router.push("/dashboard");
      })}
    >
      {pending ? "Entering OS…" : "Enter AgroSense OS →"}
    </button>
  );
}
"""

# ---------- Settings: real notifications + data export ----------
F["app/settings/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import Link from "next/link";
import { NotificationsForm } from "./NotificationsForm";
import { DataExportButton } from "./DataExportButton";

export default async function SettingsPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: profile } = await sb.from("profiles").select("notification_prefs,email,role").eq("user_id", me.user!.id).maybeSingle();
  const prefs = (profile?.notification_prefs as any) ?? {};

  return (
    <AppShell section="Settings" subtitle="Account · Security · Recovery · Data">
      <div className="grid md:grid-cols-2 gap-5">
        <Panel title="Account">
          <p className="text-sage text-sm">Email: <span className="text-pearl font-mono text-xs">{profile?.email}</span></p>
          <p className="text-sage text-sm mt-1">Role: <span className="badge badge-muted">{profile?.role ?? "user"}</span></p>
        </Panel>

        <Panel title="Security">
          <p className="text-sage text-sm">Password and session management. Use the recovery flow to rotate without resetting the wallet.</p>
          <Link href="/reset-password" className="btn-ghost mt-3 inline-block">Use recovery key →</Link>
        </Panel>

        <Panel title="Recovery">
          <p className="text-sage text-sm">Your recovery key wraps the embedded wallet. Store it offline. Lost keys cannot be regenerated without rotating the wallet — not permitted.</p>
        </Panel>

        <Panel title="Notifications">
          <NotificationsForm prefs={prefs} />
        </Panel>

        <Panel title="Data export">
          <p className="text-sage text-sm">Download every farm, case, evidence reference, and mirrored verdict as a JSON bundle.</p>
          <DataExportButton />
        </Panel>

        <Panel title="Danger zone" tone="risk">
          <p className="text-sage text-sm">Account deletion permanently removes profile and farm records. Wallet ciphertext is destroyed; the wallet becomes unrecoverable. (Coming soon.)</p>
        </Panel>
      </div>
    </AppShell>
  );
}

function Panel({ title, children, tone }: { title: string; children: React.ReactNode; tone?: "risk" }) {
  return (
    <section className={`panel p-6 ${tone === "risk" ? "border border-stormclay/30" : ""}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="font-display text-pearl text-xl">{title}</div>
        {tone === "risk" && <span className="badge badge-risk">Sensitive</span>}
      </div>
      {children}
    </section>
  );
}
"""

F["app/settings/NotificationsForm.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { updateNotificationPrefs } from "@/server/actions/settings";

export function NotificationsForm({ prefs }: { prefs: any }) {
  const [state, setState] = useState({
    verdict_email: !!prefs.verdict_email,
    risk_email:    !!prefs.risk_email,
    weekly_digest: !!prefs.weekly_digest,
  });
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();

  function toggle(key: keyof typeof state) {
    setMsg(undefined);
    const next = { ...state, [key]: !state[key] };
    setState(next);
    start(async () => {
      const r = await updateNotificationPrefs(next);
      setMsg(r.ok ? "Saved" : (r.error || "Save failed"));
    });
  }
  const Row = ({ k, label, desc }: { k: keyof typeof state; label: string; desc: string }) => (
    <label className="flex items-start justify-between gap-3 py-2 cursor-pointer">
      <div>
        <div className="text-pearl text-sm">{label}</div>
        <div className="text-sage text-xs">{desc}</div>
      </div>
      <button type="button" onClick={() => toggle(k)} disabled={pending}
        className={`relative w-10 h-6 rounded-full transition ${state[k] ? "bg-biosignal" : "bg-white/10"}`}>
        <span className={`absolute top-0.5 ${state[k] ? "left-5" : "left-0.5"} w-5 h-5 rounded-full bg-pearl transition`} />
      </button>
    </label>
  );
  return (
    <div>
      <Row k="verdict_email" label="Verdict emails"  desc="Receive an email when a GenLayer verdict lands." />
      <Row k="risk_email"    label="Risk alerts"     desc="Storm Clay severity events on cases you own." />
      <Row k="weekly_digest" label="Weekly digest"   desc="Roll-up of new verdicts and contract activity." />
      {msg && <div className="text-xs text-sage mt-2">{msg}</div>}
    </div>
  );
}
"""

F["app/settings/DataExportButton.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { exportUserData } from "@/server/actions/settings";

export function DataExportButton() {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  function onClick() {
    setErr(undefined);
    start(async () => {
      const r = await exportUserData();
      if (!r.ok) { setErr(r.error || "Export failed"); return; }
      const blob = new Blob([JSON.stringify(r.bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `agrosense-export-${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
  }
  return (
    <div className="mt-3 space-y-2">
      <button type="button" onClick={onClick} disabled={pending}
        className="btn-primary disabled:opacity-60">
        {pending ? "Bundling…" : "Download my data (JSON)"}
      </button>
      {err && <div className="text-stormclay text-sm">{err}</div>}
    </div>
  );
}
"""

# ---------- Admin: replay + export per case ----------
F["app/admin/page.tsx"] = r"""import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";
import { ConsensusBadge } from "@/components/Badges";
import { AGROSENSE_CONTRACT_ADDRESS, AGROSENSE_CONTRACT_NETWORK } from "@/lib/genlayer/contract";
import { AdminCaseActions } from "./AdminCaseActions";

export default async function AdminPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: prof } = await sb.from("profiles").select("role").eq("user_id", me.user!.id).maybeSingle();
  if (prof?.role !== "admin") redirect("/dashboard");

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,user_id,crop_type,status,created_at").order("created_at", { ascending: false }).limit(50);
  const { data: verdicts } = await sb.from("genlayer_verdicts")
    .select("*").order("created_at", { ascending: false }).limit(20);
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("*").order("created_at", { ascending: false }).limit(30);

  return (
    <AppShell section="Contract operations console" subtitle="Admin · GenLayer mirror">
      <div className="space-y-6">
        <div className="panel-violet p-5 relative scanline">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-sage">Source of truth contract</div>
              <div className="font-mono text-pearl break-all mt-1">{AGROSENSE_CONTRACT_ADDRESS}</div>
            </div>
            <ConsensusBadge label={AGROSENSE_CONTRACT_NETWORK} />
          </div>
        </div>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Case queue</div>
            <span className="badge badge-muted">{cases?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>Crop</th><th>Status</th><th>Created</th><th>User</th><th>Actions</th></tr></thead>
            <tbody>
              {(cases ?? []).map(c => (
                <tr key={c.id}>
                  <td className="font-display text-pearl">{c.crop_type}</td>
                  <td><span className="badge badge-sensor">{c.status}</span></td>
                  <td className="text-sage">{new Date(c.created_at).toLocaleString()}</td>
                  <td className="font-mono text-xs text-sage">{c.user_id.slice(0,8)}…</td>
                  <td><AdminCaseActions caseId={c.id} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <div className="font-display text-pearl text-xl mb-3">Mirrored verdicts</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(verdicts ?? []).map(v => (
              <div key={v.id} className="panel p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-pearl text-lg">{v.verdict}</div>
                  <ConsensusBadge label={v.consensus_status} />
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
                  <div><div className="text-[10px] uppercase text-sage">Risk</div><div className="text-pearl">{v.risk_level}</div></div>
                  <div><div className="text-[10px] uppercase text-sage">Plan</div><div className="text-pearl">{v.selected_plan}</div></div>
                </div>
                <div className="mt-3 flex flex-wrap gap-3"><HashText label="tx" value={v.transaction_hash} kind="tx" /><HashText label="case" value={v.advisory_case_id} /></div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4">
            <div className="font-display text-pearl text-lg">Contract activity stream</div>
            <span className="badge badge-muted">{activity?.length ?? 0}</span>
          </div>
          <table className="os mt-3">
            <thead><tr><th>When</th><th>Action</th><th>Status</th><th>Tx</th><th>Error</th></tr></thead>
            <tbody>
              {(activity ?? []).map(a => (
                <tr key={a.id}>
                  <td className="text-sage text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="text-pearl">{a.action}</td>
                  <td><span className={`badge ${a.status === "error" ? "badge-risk" : a.status === "submitted" ? "badge-sensor" : "badge-bio"}`}>{a.status}</span></td>
                  <td><HashText value={a.transaction_hash} kind="tx" /></td>
                  <td className="text-stormclay text-xs max-w-[260px] truncate">{a.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </AppShell>
  );
}
"""

F["app/admin/AdminCaseActions.tsx"] = r""""use client";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { replayCase, exportAdvisoryPacket } from "@/server/actions/admin";

export function AdminCaseActions({ caseId }: { caseId: string }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string>();
  const router = useRouter();
  function doReplay() {
    setMsg(undefined);
    if (!confirm("Replay this case? The mirrored verdict will be cleared.")) return;
    start(async () => {
      const r = await replayCase(caseId);
      if (!r.ok) { setMsg(r.error || "Replay failed"); return; }
      setMsg("Replay queued."); router.refresh();
    });
  }
  function doExport() {
    setMsg(undefined);
    start(async () => {
      const r = await exportAdvisoryPacket(caseId);
      if (!r.ok) { setMsg(r.error || "Export failed"); return; }
      const blob = new Blob([JSON.stringify(r.bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url;
      a.download = `advisory-packet-${caseId}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    });
  }
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <button onClick={doReplay}  disabled={pending} className="btn-ghost text-xs disabled:opacity-50">Replay</button>
      <button onClick={doExport}  disabled={pending} className="btn-ghost text-xs disabled:opacity-50">Export packet</button>
      {msg && <span className="text-sage">{msg}</span>}
    </div>
  );
}
"""

# ---------- Update /cases/new to expose farm coords + WeatherPullButton ----------
F["app/cases/new/page.tsx"] = r"""import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { createAdvisoryCase } from "@/server/actions/cases";
import { LeftPacketRail, RightPacketRail } from "@/components/AdvisoryPacketRails";
import { ConsensusBadge } from "@/components/Badges";
import { WeatherPullButton } from "./WeatherPullButton";

async function createCaseAction(fd: FormData) { "use server"; await createAdvisoryCase(fd); }

export default async function NewCasePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farms } = await sb.from("farms")
    .select("id,name,country,region,latitude,longitude").eq("user_id", me.user!.id);

  return (
    <AppShell section="Advisory Packet Builder" subtitle="Assemble the intelligence packet for GenLayer adjudication">
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-3 hidden lg:block"><LeftPacketRail farms={farms ?? []} /></div>

        <div className="col-span-12 lg:col-span-6 space-y-5">
          <Step n="01" t="Select farm & decision">
            <form action={createCaseAction} className="space-y-3">
              <label className="text-[10px] uppercase tracking-wider text-sage">Farm</label>
              <select name="farmId" required className="input">
                {(farms ?? []).map(f => <option key={f.id} value={f.id}>{f.name} ({f.region ?? ""}, {f.country})</option>)}
              </select>

              <label className="text-[10px] uppercase tracking-wider text-sage">Decision type</label>
              <select name="decisionType" required className="input">
                <option value="plant_now">Should I plant now?</option>
                <option value="delay_planting">Should I delay planting?</option>
                <option value="irrigate">Should I irrigate?</option>
                <option value="harvest_window">Is this harvest window safe?</option>
                <option value="risk_check">Is this farm action too risky?</option>
              </select>

              <input name="cropType" required placeholder="Crop (maize, rice, cassava…)" className="input" />
              <input name="advisoryQuestion" required className="input" placeholder="Advisory question" />
              <input name="plantingWindow" className="input" placeholder="Decision window (e.g. next 7–14 days)" />

              <div className="grid grid-cols-1 gap-3 pt-2">
                <label className="text-[10px] uppercase tracking-wider text-sage">Field observation</label>
                <textarea name="userObservation" rows={3} className="input" placeholder="What you can see from the field right now" />

                <div className="flex items-center justify-between">
                  <label className="text-[10px] uppercase tracking-wider text-sage">Weather context</label>
                  <WeatherPullButton farms={(farms ?? []).map(f => ({ id: f.id, latitude: f.latitude, longitude: f.longitude }))} />
                </div>
                <textarea name="weatherContext" rows={4} className="input" placeholder="Forecast notes — or click 'Pull live weather' above" />

                <label className="text-[10px] uppercase tracking-wider text-sage">Market context (optional)</label>
                <textarea name="marketContext" rows={2} className="input" placeholder="Price trend, demand signal" />
              </div>

              <button className="btn-primary w-full mt-3">Save draft & continue →</button>
              <p className="text-xs text-sage">You can attach up to 3 evidence files on the next step before submitting to GenLayer.</p>
            </form>
          </Step>

          <div className="panel-violet p-6 relative scanline">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-sage">GenLayer Review</div>
                <div className="font-display text-pearl text-xl mt-1">Validator consensus</div>
              </div>
              <ConsensusBadge label="Source of truth" />
            </div>
            <p className="text-pearl/80 text-sm mt-3 leading-relaxed">
              This case will be evaluated by GenLayer validators. AgroSense prepares the advisory
              packet, but the final verdict is not produced by the frontend, Supabase, or any
              private backend. Validators independently reason over the evidence and reach
              consensus on the most defensible advisory outcome.
            </p>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 hidden lg:block"><RightPacketRail /></div>
      </div>
    </AppShell>
  );
}

function Step({ n, t, children }: { n: string; t: string; children: React.ReactNode }) {
  return (
    <section className="panel p-6">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs text-sage">STEP {n}</span>
        <div className="font-display text-pearl text-xl">{t}</div>
      </div>
      <div className="hr my-4" />
      {children}
    </section>
  );
}
"""

def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage6] wrote {n} files")

if __name__ == "__main__":
    main()
