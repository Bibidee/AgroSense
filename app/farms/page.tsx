import { supabaseServer } from "@/lib/supabase/server";
import { AppShell } from "@/components/AppShell";
import { createFarm } from "@/server/actions/farms";

async function createFarmAction(fd: FormData) { "use server"; await createFarm(fd); }

export default async function FarmsPage() {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  const { data: farms } = await sb.from("farms").select("*").eq("user_id", me.user!.id).order("created_at", { ascending: false });

  return (
    <AppShell section="Farm registry" subtitle="Plots, crops, irrigation, coordinates">
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="font-display text-3xl text-pearl">Your farms</h1>
            <span className="badge badge-muted">{farms?.length ?? 0} registered</span>
          </div>
          {(farms ?? []).length === 0 && (
            <div className="panel p-10 text-center text-sage">No farms yet. Add your first farm to start advisory cases.</div>
          )}
          {(farms ?? []).map(f => (
            <div key={f.id} className="panel p-5 lift">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-display text-pearl text-xl">{f.name}</div>
                  <div className="text-sage text-sm">{f.region ? `${f.region}, ` : ""}{f.country}{f.nearest_town ? ` · ${f.nearest_town}` : ""}</div>
                </div>
                <span className="badge badge-bio">Active</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-sm">
                <Cell k="Size" v={f.farm_size ? `${f.farm_size} ha` : "—"} />
                <Cell k="Soil" v={f.soil_type ?? "—"} />
                <Cell k="Irrigation" v={f.irrigation_available ? "Yes" : "No"} />
                <Cell k="Crops" v={f.main_crops?.length ? f.main_crops.join(", ") : "—"} />
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-12 lg:col-span-5">
          <div className="panel-ivory p-6 light-surface">
            <span className="badge badge-bio">Add farm</span>
            <h2 className="font-display text-2xl text-soil mt-2">Register a new plot</h2>
            <p className="text-soil/60 text-sm mt-1">Used to anchor advisory cases and signal context.</p>
            <form action={createFarmAction} className="space-y-3 mt-5">
              <input name="name" required placeholder="Farm name" className="input-light" />
              <div className="grid grid-cols-2 gap-3">
                <input name="country" required placeholder="Country" className="input-light" />
                <input name="region" placeholder="State / region" className="input-light" />
              </div>
              <input name="nearestTown" placeholder="Nearest town" className="input-light" />
              <div className="grid grid-cols-2 gap-3">
                <input name="latitude"  type="number" step="any" placeholder="Latitude"  className="input-light" />
                <input name="longitude" type="number" step="any" placeholder="Longitude" className="input-light" />
              </div>
              <input name="farmSize" type="number" step="any" placeholder="Farm size (ha)" className="input-light" />
              <input name="soilType" placeholder="Soil type" className="input-light" />
              <input name="mainCrops" placeholder="Main crops (comma separated)" className="input-light" />
              <label className="flex items-center gap-2 text-sm text-soil">
                <input name="irrigationAvailable" type="checkbox" /> Irrigation available
              </label>
              <input name="previousPlantingDate" type="date" className="input-light" />
              <button className="btn-primary w-full">Register farm</button>
            </form>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Cell({ k, v }: { k: string; v: string }) {
  return <div><div className="text-[10px] uppercase text-sage">{k}</div><div className="text-pearl mt-1">{v}</div></div>;
}
