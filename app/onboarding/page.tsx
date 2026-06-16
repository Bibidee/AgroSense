import Link from "next/link";
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
