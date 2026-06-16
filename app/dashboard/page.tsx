import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { VerdictCapsule } from "@/components/VerdictCapsule";
import { VerdictRotator } from "@/components/VerdictRotator";
import { GenLayerConsensusPanel } from "@/components/GenLayerConsensusPanel";
import { WeatherRiskOrb } from "@/components/WeatherRiskOrb";
import { SignalStrip } from "@/components/SignalStrip";
import { EvidenceStrengthMeter } from "@/components/EvidenceStrengthMeter";
import { CropWindowTimeline } from "@/components/CropWindowTimeline";
import { ContractActivityStream } from "@/components/ContractActivityStream";
import { FarmsWeatherGrid } from "@/components/FarmsWeatherGrid";
import { OperatorWeather } from "@/components/OperatorWeather";
import { AutoRefresh } from "@/components/AutoRefresh";
import { LiveBadge } from "@/components/Badges";

export default async function DashboardPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const userId = me.user!.id;

  const { data: cases } = await sb.from("advisory_cases")
    .select("id,crop_type,status,created_at,decision_type").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(8);
  const { data: verdictList } = await sb.from("genlayer_verdicts")
    .select("*").eq("user_id", userId).order("created_at", { ascending: false }).limit(8);
  const latest = verdictList?.[0] ?? null;
  const { data: activity } = await sb.from("contract_activity_logs")
    .select("action,status,transaction_hash,created_at").eq("user_id", userId)
    .order("created_at", { ascending: false }).limit(5);

  return (
    <AppShell section="Mission control" subtitle="Live agricultural decision OS">
      <AutoRefresh />
      <div className="space-y-6">
        <SignalStrip />

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-7">
            <VerdictRotator verdicts={verdictList ?? []} />
          </div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-2"><WeatherRiskOrb /></div>
          <div className="col-span-12 sm:col-span-6 lg:col-span-3">
            <GenLayerConsensusPanel v={latest} status={latest ? "consensus_reached" : "not_submitted"} />
          </div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-4"><OperatorWeather /></div>
          <div className="col-span-12 lg:col-span-8"><FarmsWeatherGrid /></div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8">
            <div className="panel overflow-hidden">
              <div className="flex items-center justify-between px-5 pt-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-sage">Active case matrix</div>
                  <div className="font-display text-pearl text-lg">Recent advisories</div>
                </div>
                <div className="flex items-center gap-2">
                  <Link href="/cases" className="btn-ghost text-sm">All cases</Link>
                  <Link href="/cases/new" className="btn-primary text-sm">+ New case</Link>
                </div>
              </div>
              <table className="os mt-3">
                <thead><tr><th>Crop</th><th>Decision</th><th>Status</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {(cases ?? []).length === 0 && (
                    <tr><td colSpan={5} className="text-center text-sage py-10">No cases yet. Open a new advisory to engage GenLayer validators.</td></tr>
                  )}
                  {(cases ?? []).map(c => (
                    <tr key={c.id}>
                      <td className="font-display text-pearl">{c.crop_type}</td>
                      <td className="text-pearl/80">{c.decision_type}</td>
                      <td><span className="badge badge-sensor">{c.status}</span></td>
                      <td className="text-sage">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td><Link href={`/cases/${c.id}`} className="text-biosignal">Open →</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4"><EvidenceStrengthMeter score={latest ? 78 : 35} /></div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 lg:col-span-8"><CropWindowTimeline /></div>
          <div className="col-span-12 lg:col-span-4"><ContractActivityStream items={activity ?? []} /></div>
        </div>
      </div>
    </AppShell>
  );
}
