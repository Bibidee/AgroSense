import { supabaseServer } from "@/lib/supabase/server";
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
