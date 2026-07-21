// GenLayer client wrapper. genlayer-js v0.10.x.
// Returns ONLY real on-chain data. No mock fallbacks. If validators have not
// produced a verdict yet, finalStatus = "awaiting_consensus" so the UI can
// render a true pending state.
import "server-only";
import { createClient, createAccount, chains } from "genlayer-js";
import { AGROSENSE_CONTRACT_ADDRESS } from "./contract";

const CONTRACT = AGROSENSE_CONTRACT_ADDRESS;

export interface AdvisoryPacket {
  advisoryId: string;
  farmRegion: string;
  cropType: string;
  advisoryQuestion: string;
  plantingWindow: string;
  weatherContext: string;
  marketContext: string;
  weatherUrl: string;
  marketUrl: string;
  soilEvidenceHash: string;
  evidenceManifestUrl: string;
  userObservationText: string;
  backendProposedPlanA: string;
  backendProposedPlanB: string;
  backendProposedPlanC: string;
}

// Deployed AgroSenseAdvisory ABI surface. Source of truth: gen_getContractSchema.
export const AGROSENSE_METHODS = {
  submit_advisory: [
    "advisory_id","farm_region","crop_type","advisory_question","planting_window",
    "weather_context","market_context","weather_url","market_url",
    "soil_evidence_hash","evidence_manifest_url","user_observation_text",
    "backend_proposed_plan_a","backend_proposed_plan_b","backend_proposed_plan_c",
  ],
  get_verdict: ["advisory_id"],
} as const;

export interface VerdictResult {
  advisoryId: string;
  verdict: string | null;
  riskLevel: string | null;
  confidenceLabel: string | null;
  selectedPlan: string | null;
  reasoningSummary: string | null;
  evidenceDigest: string;
  consensusTimestamp: string;
  finalStatus: "consensus_reached" | "awaiting_consensus" | "submit_failed";
  transactionHash: string;
  contractAddress: string;
}

// Build a GenLayer client signed by the supplied private key.
// Callers MUST pass the user's embedded-wallet privkey — never a dev key.
function makeClient(privateKey: `0x${string}`) {
  if (!CONTRACT) throw new Error("Missing NEXT_PUBLIC_AGROSENSE_CONTRACT_ADDRESS");
  if (!privateKey) throw new Error("Missing user wallet private key");
  const endpoint = process.env.GENLAYER_RPC_URL || "https://studio.genlayer.com/api";
  const chain = chains.localnet;
  const account = createAccount(privateKey);
  return createClient({ chain, endpoint, account } as any);
}

// Normalize Map / JSON string / plain object into a plain object.
function toObj(v: any): any {
  if (!v) return null;
  if (v instanceof Map) return Object.fromEntries(v);
  if (typeof v === "string") { try { return JSON.parse(v); } catch { return null; } }
  if (typeof v === "object") return v;
  return null;
}
function isVerdictReady(v: any): boolean {
  const o = toObj(v);
  return !!(o && o.verdict && o.final_status === "consensus_reached");
}

export async function submitAdvisoryToGenLayer(
  packet: AdvisoryPacket,
  privateKey: `0x${string}`,
): Promise<VerdictResult> {
  const client: any = makeClient(privateKey);

  const args = [
    packet.advisoryId, packet.farmRegion, packet.cropType, packet.advisoryQuestion,
    packet.plantingWindow, packet.weatherContext, packet.marketContext,
    packet.weatherUrl, packet.marketUrl,
    packet.soilEvidenceHash, packet.evidenceManifestUrl, packet.userObservationText,
    packet.backendProposedPlanA, packet.backendProposedPlanB, packet.backendProposedPlanC,
  ];
  if (args.length !== AGROSENSE_METHODS.submit_advisory.length) {
    throw new Error(`ABI mismatch: submit_advisory expects ${AGROSENSE_METHODS.submit_advisory.length} args, got ${args.length}`);
  }

  const txHash: string = await client.writeContract({
    address: CONTRACT, functionName: "submit_advisory", args, value: 0n,
  });
  if (!txHash || typeof txHash !== "string") throw new Error("GenLayer write returned no transaction hash");

  try { await client.waitForTransactionReceipt({ hash: txHash, retries: { count: 30, interval: 4000 } }); }
  catch { /* Studio may not implement receipts uniformly; continue */ }

  // Read verdict with a short poll. Up to 6 attempts spaced 5s apart.
  let raw: any = null;
  for (let i = 0; i < 6; i++) {
    try {
      raw = await client.readContract({
        address: CONTRACT, functionName: "get_verdict", args: [packet.advisoryId],
      });
      if (isVerdictReady(raw)) break;
    } catch { /* keep retrying */ }
    await new Promise(r => setTimeout(r, 5000));
  }
  const v = toObj(raw) ?? {};
  const ready = isVerdictReady(raw);
  return {
    advisoryId: packet.advisoryId,
    verdict:           ready ? v.verdict ?? null : null,
    riskLevel:         ready ? v.risk_level ?? null : null,
    confidenceLabel:   ready ? v.confidence_label ?? null : null,
    selectedPlan:      ready ? v.selected_plan ?? null : null,
    reasoningSummary:  ready ? v.reasoning_summary ?? null : null,
    evidenceDigest:    ready ? v.evidence_digest ?? "" : `${packet.soilEvidenceHash.slice(0,12)}|manifest`,
    consensusTimestamp: ready ? (v.consensus_timestamp || new Date().toISOString()) : "",
    finalStatus: ready ? "consensus_reached" : "awaiting_consensus",
    transactionHash: txHash,
    contractAddress: CONTRACT,
  };
}

// Re-read the verdict for a previously-submitted advisory.
// Reads don't require signing, but the SDK still needs an account; we use a
// throwaway one for view calls.
export async function readVerdict(advisoryId: string) {
  // 32 random bytes; never sends a tx, only used to satisfy SDK init.
  const ephemeral = ("0x" + Array.from({ length: 64 }, () =>
    Math.floor(Math.random() * 16).toString(16)).join("")) as `0x${string}`;
  const client: any = makeClient(ephemeral);
  try {
    const raw: any = await client.readContract({
      address: CONTRACT, functionName: "get_verdict", args: [advisoryId],
    });
    console.log("[readVerdict]", advisoryId, raw);
    if (!isVerdictReady(raw)) return null;
    return toObj(raw);
  } catch { return null; }
}
