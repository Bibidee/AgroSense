# v0.4.0
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json
import typing

VmUserError = gl.vm.UserError

CANONICAL_VERDICTS = (
    "plant_now",
    "delay_planting",
    "irrigate_first",
    "proceed_with_caution",
    "avoid_action",
    "request_more_evidence",
)


def _canon(text: str) -> str:
    t = (text or "").lower().strip()
    for token in CANONICAL_VERDICTS:
        if token in t:
            return token
    if "request" in t or "more evidence" in t:          return "request_more_evidence"
    if "avoid" in t:                                     return "avoid_action"
    if "irrigat" in t:                                   return "irrigate_first"
    if "delay" in t or "wait" in t or "postpone" in t:  return "delay_planting"
    if "caution" in t or "monitor" in t:                 return "proceed_with_caution"
    if "plant" in t or "proceed" in t:                   return "plant_now"
    return "request_more_evidence"


def _summarise_documents(manifest_json: str) -> str:
    """
    Parse the evidence manifest and return a readable summary of every
    document's extracted text.  Falls back gracefully on bad JSON.
    """
    try:
        manifest = json.loads(manifest_json)
    except Exception:
        return "(evidence manifest could not be parsed)"

    docs = manifest.get("documents", [])
    if not docs:
        return "(no documents attached)"

    parts = []
    for doc in docs:
        name = doc.get("name", "unknown")
        text = (doc.get("extracted_text") or "").strip()
        sha  = (doc.get("sha256") or "")[:16]
        if text:
            parts.append(f"--- {name} (sha256:{sha}...) ---\n{text[:3000]}")
        else:
            parts.append(f"--- {name} (sha256:{sha}...) --- [binary / no text extracted]")

    return "\n\n".join(parts)


class AgroSenseAdvisory(gl.Contract):
    verdicts:  TreeMap[str, str]
    submitted: TreeMap[str, str]

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    @gl.public.view
    def get_verdict(self, advisory_id: str) -> dict:
        raw = self.verdicts.get(advisory_id, "")
        if not raw:
            return {"final_status": "not_found"}
        return json.loads(raw)

    @gl.public.view
    def get_submitter(self, advisory_id: str) -> str:
        return self.submitted.get(advisory_id, "")

    # ------------------------------------------------------------------
    @gl.public.write
    def submit_advisory(
        self,
        advisory_id: str,
        farm_region: str,
        crop_type: str,
        advisory_question: str,
        planting_window: str,
        weather_context: str,
        market_context: str,
        weather_url: str,
        market_url: str,
        soil_evidence_hash: str,
        evidence_manifest_url: str,
        user_observation_text: str,
        backend_proposed_plan_a: str,
        backend_proposed_plan_b: str,
        backend_proposed_plan_c: str,
    ) -> str:

        # ------ Build deterministic case packet (no I/O here) ------
        case = {
            "advisory_id": advisory_id,
            "farm_region": farm_region,
            "crop_type": crop_type,
            "advisory_question": advisory_question,
            "planting_window": planting_window,
            "weather_context": weather_context,
            "market_context": market_context,
            "soil_evidence_hash": soil_evidence_hash,
            "user_observation": user_observation_text,
            "plan_a": backend_proposed_plan_a,
            "plan_b": backend_proposed_plan_b,
            "plan_c": backend_proposed_plan_c,
        }
        case_json = json.dumps(case, indent=2, sort_keys=True)

        # ------ All nondeterministic work in a single leader function ------
        # Nested exactly one call-frame deep from submit_advisory so the web
        # fetch and both LLM calls run as one unit.  A single
        # prompt_comparative judgment replaces the three separate consensus
        # rounds that existed in v0.3.0.
        def leader_fn() -> str:
            # 1. Fetch the evidence manifest
            try:
                resp = gl.nondet.web.get(evidence_manifest_url)
                manifest_json = resp.body.decode("utf-8")
            except Exception:
                manifest_json = "{}"

            document_summary = _summarise_documents(manifest_json)
            evidence_section = "\n\nATTACHED EVIDENCE DOCUMENTS:\n" + document_summary

            # 2. Verdict token
            token_raw = gl.nondet.exec_prompt(
                "You are an independent agricultural advisory validator.\n\n"
                "Case:\n" + case_json + evidence_section + "\n\n"
                "Choose the MOST DEFENSIBLE single action for the next 7-14 days "
                "from this enum. Return EXACTLY one token, lowercase, no other "
                "characters:\n\n"
                "  plant_now\n"
                "  delay_planting\n"
                "  irrigate_first\n"
                "  proceed_with_caution\n"
                "  avoid_action\n"
                "  request_more_evidence\n\n"
                "Output: only the token. No prose, no JSON, no punctuation."
            )
            token = _canon(token_raw)

            # 3. Reasoning (uses token from step 2)
            reason_raw = gl.nondet.exec_prompt(
                "The agreed advisory action is: " + token + ".\n\n"
                "Case:\n" + case_json + evidence_section + "\n\n"
                "Produce a concise JSON object describing the verdict. Use these "
                "exact keys:\n"
                "{\n"
                '  "risk_level": "<low|moderate|high>",\n'
                '  "confidence": "<weak|moderate|strong>",\n'
                '  "selected_plan": "<A|B|C>",\n'
                '  "reasoning": "<1-2 sentences explaining why '
                + token + ' is most defensible>"\n'
                "}\n\n"
                "Return only JSON. Wording of reasoning may vary; content must "
                "defend the agreed action."
            )

            return json.dumps(
                {"token": token, "reasoning_raw": reason_raw.strip()},
                sort_keys=True,
            )

        principle = (
            "Both outputs must be JSON objects with matching 'token' fields. "
            "The token must be exactly one of: plant_now, delay_planting, "
            "irrigate_first, proceed_with_caution, avoid_action, "
            "request_more_evidence. "
            "The 'reasoning_raw' fields must both defend the same token; "
            "minor wording differences are acceptable, but different tokens are not."
        )

        result_raw = gl.eq_principle.prompt_comparative(leader_fn, principle=principle)

        try:
            result = json.loads(result_raw)
        except Exception:
            result = {}

        agreed_token = _canon(result.get("token", ""))
        if agreed_token not in CANONICAL_VERDICTS:
            agreed_token = "request_more_evidence"

        try:
            parsed = json.loads(result.get("reasoning_raw", "{}"))
        except Exception:
            parsed = {}

        stored = {
            "advisory_id": advisory_id,
            "verdict": agreed_token,
            "risk_level":        parsed.get("risk_level", "moderate"),
            "confidence_label":  parsed.get("confidence", "moderate"),
            "selected_plan":     parsed.get("selected_plan", "B"),
            "reasoning_summary": (parsed.get("reasoning") or "")[:400],
            "evidence_digest":   "soil:" + (soil_evidence_hash or "")[:12]
                                 + "|manifest:" + evidence_manifest_url[-24:],
            "consensus_timestamp": "",
            "final_status": "consensus_reached",
        }
        self.verdicts[advisory_id] = json.dumps(stored, sort_keys=True)
        self.submitted[advisory_id] = str(gl.message.sender_address)
        return advisory_id
