import { supabaseServer } from "@/lib/supabase/server";
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
