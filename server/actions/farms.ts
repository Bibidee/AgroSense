"use server";
import { redirect } from "next/navigation";
import { supabaseServer } from "@/lib/supabase/server";
import { farmSchema } from "@/lib/validation/schemas";

export async function createFarm(formData: FormData) {
  const sb = await supabaseServer();
  const { data: me } = await sb.auth.getUser();
  if (!me.user) return { ok: false, error: "Not authenticated." };

  const parsed = farmSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { ok: false, error: "Invalid farm details." };

  const v = parsed.data;
  const { error } = await sb.from("farms").insert({
    user_id: me.user.id,
    name: v.name,
    country: v.country,
    region: v.region ?? null,
    latitude: v.latitude ?? null,
    longitude: v.longitude ?? null,
    nearest_town: v.nearestTown ?? null,
    farm_size: v.farmSize ?? null,
    soil_type: v.soilType ?? null,
    irrigation_available: !!v.irrigationAvailable,
    main_crops: v.mainCrops ? v.mainCrops.split(",").map((s) => s.trim()) : [],
    previous_planting_date: v.previousPlantingDate || null,
  });
  if (error) return { ok: false, error: error.message };
  redirect("/farms");
}
