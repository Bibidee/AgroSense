import { redirect } from "next/navigation";
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
