"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Re-renders the parent server component on a timer so server-fetched data
// (Open-Meteo, Supabase reads) refreshes without a manual reload.
// Default: 10 minutes — Open-Meteo updates hourly, so this catches new
// hourly slices within ~10 min while staying friendly to the free tier.
export function AutoRefresh({ intervalMs = 10 * 60 * 1000 }: { intervalMs?: number }) {
  const router = useRouter();
  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === "visible") router.refresh();
    }, intervalMs);
    // Also refresh as soon as the tab regains focus after being hidden.
    function onVis() { if (document.visibilityState === "visible") router.refresh(); }
    document.addEventListener("visibilitychange", onVis);
    return () => { clearInterval(id); document.removeEventListener("visibilitychange", onVis); };
  }, [intervalMs, router]);
  return null;
}
