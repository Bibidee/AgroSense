import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { HashText } from "@/components/HashText";
import { ExportKeyForm } from "./ExportKeyForm";

export default async function ProfilePage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: profile } = await sb.from("profiles").select("*").eq("user_id", me.user!.id).maybeSingle();
  const { data: wallet }  = await sb.from("wallets").select("address,created_at").eq("user_id", me.user!.id).maybeSingle();
  const { data: audit }   = await sb.from("recovery_audit_logs").select("*").eq("user_id", me.user!.id).order("created_at",{ascending:false}).limit(10);

  return (
    <AppShell section="Operator profile" subtitle="Identity, embedded wallet, recovery audit">
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7 space-y-5">
          <section className="panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-sage">Email profile</div>
                <div className="font-display text-2xl text-pearl mt-1">{profile?.email}</div>
              </div>
              <span className="badge badge-bio">Active</span>
            </div>
          </section>

          <section className="panel p-6">
            <div className="text-[10px] uppercase tracking-wider text-sage">Embedded wallet</div>
            <div className="font-mono text-pearl mt-2 break-all">{wallet?.address}</div>
            <p className="text-sage text-sm mt-3">
              Your wallet is embedded into your AgroSense profile. It is used to sign GenLayer
              actions in the background. You do not need MetaMask, Rabby, Rainbow, Zerion, or
              any external wallet for normal use.
            </p>
            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              <div><div className="text-[10px] uppercase text-sage">Status</div><div className="text-pearl mt-1">Attached</div></div>
              <div><div className="text-[10px] uppercase text-sage">Created</div><div className="text-pearl mt-1">{wallet?.created_at ? new Date(wallet.created_at).toLocaleDateString() : "—"}</div></div>
            </div>
          </section>

          <ExportKeyForm />
        </div>

        <div className="col-span-12 lg:col-span-5">
          <section className="panel p-6">
            <div className="text-[10px] uppercase tracking-wider text-sage">Recovery audit log</div>
            <ul className="mt-4 space-y-3">
              {(audit ?? []).length === 0 && <li className="text-sage text-sm">No recovery events.</li>}
              {(audit ?? []).map(a => (
                <li key={a.id} className="flex items-start gap-3">
                  <i className={`dot mt-1.5 ${a.action === "privkey_exported" ? "dot-risk" : "dot-bio"}`}></i>
                  <div>
                    <div className="text-pearl text-sm">{a.action}</div>
                    <div className="text-sage text-xs">{new Date(a.created_at).toLocaleString()}</div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
