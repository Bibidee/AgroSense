# v0.2.17 
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
    # Exact token match
    for token in CANONICAL_VERDICTS:
        if token in t:
            return token
    # Fuzzy fallbacks
    if "request" in t or "more evidence" in t:         return "request_more_evidence"
    if "avoid" in t:                                   return "avoid_action"
    if "irrigat" in t:                                 return "irrigate_first"
    if "delay" in t or "wait" in t or "postpone" in t: return "delay_planting"
    if "caution" in t or "monitor" in t:               return "proceed_with_caution"
    if "plant" in t or "proceed" in t:                 return "plant_now"
    return "request_more_evidence"


class AgroSenseAdvisory(gl.Contract):
    # advisory_id -> json struct stored on-chain
    verdicts: TreeMap[str, str]
    # advisory_id -> submitter address (string form)
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
        uploaded_evidence_hash: str,
        user_observation_text: str,
        backend_proposed_plan_a: str,
        backend_proposed_plan_b: str,
        backend_proposed_plan_c: str,
    ) -> str:
        case = {
            "advisory_id": advisory_id,
            "farm_region": farm_region,
            "crop_type": crop_type,
            "advisory_question": advisory_question,
            "planting_window": planting_window,
            "weather_context": weather_context,
            "market_context": market_context,
            "weather_url": weather_url,
            "market_url": market_url,
            "soil_evidence_hash": soil_evidence_hash,
            "uploaded_evidence_hash": uploaded_evidence_hash,
            "user_observation": user_observation_text,
            "plan_a": backend_proposed_plan_a,
            "plan_b": backend_proposed_plan_b,
            "plan_c": backend_proposed_plan_c,
        }
        case_json = json.dumps(case, indent=2, sort_keys=True)

        # ---------- Stage 1: action token (strict consensus) ----------
        token_prompt = (
            "You are an independent agricultural advisory validator.\n\n"
            "Case:\n" + case_json + "\n\n"
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

        def token_callback() -> str:
            raw = gl.nondet.exec_prompt(token_prompt)
            return _canon(raw)

        agreed_token = gl.eq_principle.strict_eq(token_callback)
        if agreed_token not in CANONICAL_VERDICTS:
            agreed_token = "request_more_evidence"

        # ---------- Stage 2: reasoning + risk + confidence (relaxed) ----------
        reason_prompt = (
            "The agreed advisory action is: " + agreed_token + ".\n\n"
            "Case:\n" + case_json + "\n\n"
            "Produce a concise JSON object describing the verdict. Use these "
            "exact keys:\n"
            "{\n"
            '  "risk_level": "<low|moderate|high>",\n'
            '  "confidence": "<weak|moderate|strong>",\n'
            '  "selected_plan": "<A|B|C>",\n'
            '  "reasoning": "<1-2 sentences explaining why '
            + agreed_token + ' is most defensible>"\n'
            "}\n\n"
            "Return only JSON. Wording of reasoning may vary; content must "
            "defend the agreed action."
        )

        def reason_callback() -> str:
            return gl.nondet.exec_prompt(reason_prompt).strip()

        principle = (
            "Both outputs must be JSON objects with keys risk_level, "
            "confidence, selected_plan, and reasoning. The reasoning field "
            "must justify the action '" + agreed_token + "'. Minor wording "
            "differences are acceptable; substantive disagreement on the "
            "action is not."
        )

        agreed_reason_raw = gl.eq_principle.prompt_comparative(
            reason_callback, principle=principle
        )

        try:
            parsed = json.loads(agreed_reason_raw)
        except Exception:
            parsed = {
                "risk_level": "moderate",
                "confidence": "moderate",
                "selected_plan": "B",
                "reasoning": (agreed_reason_raw or "")[:280],
            }

        evidence_digest = (
            "soil:" + (soil_evidence_hash or "")[:12]
            + "|files:" + (uploaded_evidence_hash or "")[:12]
        )

        stored = {
            "advisory_id": advisory_id,
            "verdict": agreed_token,
            "risk_level":       parsed.get("risk_level", "moderate"),
            "confidence_label": parsed.get("confidence", "moderate"),
            "selected_plan":    parsed.get("selected_plan", "B"),
            "reasoning_summary": (parsed.get("reasoning") or "")[:400],
            "evidence_digest": evidence_digest,
            "consensus_timestamp": "",
            "final_status": "consensus_reached",
        }
        self.verdicts[advisory_id] = json.dumps(stored, sort_keys=True)
        self.submitted[advisory_id] = str(gl.message.sender_address)
        return advisory_id