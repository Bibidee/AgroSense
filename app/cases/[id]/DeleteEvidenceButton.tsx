"use client";
import { useTransition, useState } from "react";
import { useRouter } from "next/navigation";
import { deleteEvidence } from "@/server/actions/evidence";

export function DeleteEvidenceButton({ evidenceId }: { evidenceId: string }) {
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string>();
  const router = useRouter();
  return (
    <>
      <button type="button" disabled={pending}
        onClick={() => {
          setErr(undefined);
          start(async () => {
            const r = await deleteEvidence(evidenceId);
            if (!r.ok) setErr(r.error || "Delete failed");
            else router.refresh();
          });
        }}
        className="text-xs text-stormclay hover:text-stormclay/80 px-2 py-1 rounded-md border border-stormclay/30 disabled:opacity-50">
        {pending ? "Removing…" : "Remove"}
      </button>
      {err && <span className="text-[10px] text-stormclay ml-2">{err}</span>}
    </>
  );
}
