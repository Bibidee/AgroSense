import { z } from "zod";

export const emailPasswordSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(200),
});

export const farmSchema = z.object({
  name: z.string().min(1).max(120),
  country: z.string().min(2).max(80),
  region: z.string().max(120).optional(),
  latitude: z.coerce.number().optional(),
  longitude: z.coerce.number().optional(),
  nearestTown: z.string().max(120).optional(),
  farmSize: z.coerce.number().nonnegative().optional(),
  soilType: z.string().max(120).optional(),
  irrigationAvailable: z.coerce.boolean().optional(),
  mainCrops: z.string().optional(),                  // CSV
  previousPlantingDate: z.string().optional(),
});

export const advisoryCaseSchema = z.object({
  farmId: z.string().uuid(),
  cropType: z.string().min(1),
  advisoryQuestion: z.string().min(5),
  decisionType: z.enum(["plant_now","delay_planting","irrigate","harvest_window","risk_check"]),
  plantingWindow: z.string().optional(),
  userObservation: z.string().max(2000).optional(),
  weatherContext: z.string().max(4000).optional(),
  marketContext: z.string().max(2000).optional(),
});

export const recoverySchema = z.object({
  email: z.string().email(),
  recoveryKey: z.string().min(20),
  newPassword: z.string().min(8),
});
