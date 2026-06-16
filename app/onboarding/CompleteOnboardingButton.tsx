"use client";
import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { markOnboardingComplete } from "@/server/actions/settings";

export function CompleteOnboardingButton({ enabled }: { enabled: boolean }) {
  const [pending, start] = useTransition();
  const router = useRouter();
  return (
    <button
      disabled={!enabled || pending}
      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      onClick={() => start(async () => {
        const r = await markOnboardingComplete();
        if (r.ok) router.push("/dashboard");
      })}
    >
      {pending ? "Entering OS…" : "Enter AgroSense OS →"}
    </button>
  );
}
