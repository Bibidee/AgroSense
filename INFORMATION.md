# AgroSense — Project Information

**Live URL:** https://the-agrosense.vercel.app  
**Repository:** https://github.com/Bibidee/AgroSense  
**Date:** July 2026

---

## Overview

AgroSense is a farm advisory platform that delivers AI-powered verdicts backed by on-chain consensus. Farmers submit advisory cases — covering decisions like planting timing, irrigation, harvesting windows, and risk checks — and receive a verdict that no single server or model can produce alone. The verdict is the result of multiple independent AI validators reaching agreement on-chain via GenLayer.

---

## The Problem It Solves

Agricultural advisory tools today either rely on a single AI model (which can be wrong and has no accountability) or on centralised services that farmers must trust blindly. AgroSense removes that single point of failure: the advisory outcome is enforced by a decentralised validator network, making the verdict auditable, tamper-resistant, and consensus-backed.

---

## How It Works

### 1. Case Creation
A farmer selects their registered farm, specifies the decision type (e.g. "Should I plant now?"), enters crop type, advisory question, field observations, and a planting window. Live weather data can be pulled automatically from the farm's GPS coordinates.

### 2. Evidence Upload
Up to 3 evidence files (soil reports, agronomy notes, lab results, photos) can be attached before submission. PDF files are parsed on upload and their extracted text is stored. This text is what validators actually read — not just a file hash.

### 3. Evidence Manifest
A public JSON endpoint is generated per case:

```
GET /api/evidence/<case-id>
```

This returns the soil evidence hash plus every attached document's name, MIME type, SHA-256, and extracted text. GenLayer validators fetch this URL live during execution — the contract never receives a static snapshot.

### 4. GenLayer Adjudication (Single-Round Consensus)

The `AgroSenseAdvisory` Intelligent Contract (v0.5.0) runs on GenLayer StudioNet. All nondeterministic work happens inside one `leader_fn`, wrapped in a single `prompt_comparative` call:

**Inside `leader_fn` (one execution unit per validator):**

1. **Fetch evidence manifest** — `gl.nondet.web.get(evidence_manifest_url)` retrieves the live JSON, including all extracted PDF text
2. **Select verdict token** — `gl.nondet.exec_prompt(...)` applies ordered decision rules to pick one of six canonical tokens
3. **Generate reasoning** — a second `gl.nondet.exec_prompt(...)` produces a JSON object with risk level, confidence, selected plan, and 1–2 sentence justification

**Canonical verdict tokens:**

| Token | Meaning |
|---|---|
| `plant_now` | Conditions are clearly favourable — proceed |
| `delay_planting` | Wait — conditions are not ready |
| `irrigate_first` | Irrigate before taking any other action |
| `proceed_with_caution` | Action is viable but risks exist |
| `avoid_action` | Do not take the proposed action |
| `request_more_evidence` | Insufficient data to advise |

**Token selection uses ordered tie-breaking rules** so validators converge on the same answer even when multiple tokens are defensible:

1. Critical disease, pest, or flood risk → `avoid_action`
2. Moisture or irrigation data missing → `request_more_evidence`
3. Moisture below germination threshold, no rain forecast within 7 days → `irrigate_first`
4. Borderline conditions but rain forecast within 7 days OR subsoil moisture adequate → `proceed_with_caution`
5. Topsoil insufficient, no rain forecast, no irrigation → `delay_planting`
6. Moisture, temperature, and timing all clearly favourable → `plant_now`

**One `prompt_comparative` judgment** is applied to the combined structured output `{token, reasoning_raw}` from all validators. Near-matches between `proceed_with_caution` and adjacent tokens are accepted; substantively different tokens are not.

### 5. Verdict Display
The finalised verdict is stored on-chain and mirrored to Supabase for fast UI reads. The case page polls for consensus and switches to **Consensus Verdict Terminal** when reached, showing the token, risk level, confidence, reasoning, transaction hash, and a link to the GenLayer explorer.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js 15 (App Router, Server Actions) |
| Database & Auth | Supabase (Postgres + Row Level Security + Storage) |
| PDF extraction | `pdf-parse` (Node.js, server-side on upload) |
| On-chain AI | GenLayer StudioNet |
| Intelligent Contract | Python (`genlayer` SDK) — v0.2.17 |
| Deployment | Vercel (function timeout extended to 300s for consensus wait) |

---

## Key Pages

| Route | Purpose |
|---|---|
| `/dashboard` | Farm overview and recent verdict feed |
| `/farms` | Register and manage farms |
| `/cases` | All advisory cases |
| `/cases/new` | Advisory Packet Builder — case + weather + market context |
| `/cases/[id]` | Case detail, evidence vault, GenLayer submit, live verdict polling |
| `/evidence` | Evidence file management |
| `/api/evidence/[caseId]` | Public evidence manifest — fetched by GenLayer validators |
| `/onboarding` | New user setup + embedded wallet creation |
| `/profile` | Wallet + encrypted key export |
| `/settings` | Notification preferences + data export |
| `/admin` | Admin case management |

---

## Data Flow

```
Farmer uploads PDF
      │
      ▼
pdf-parse extracts text → stored in Supabase evidence_files
      │
      ▼
Farmer submits case
      │
      ▼
Next.js Server Action builds advisory packet
      │  includes: evidence_manifest_url = /api/evidence/<caseId>
      ▼
GenLayer StudioNet
      │
      ├──► Validator A ─┐
      ├──► Validator B ─┤  each runs leader_fn:
      ├──► Validator C ─┤  1. web.get(evidence_manifest_url) — reads PDF text live
      ├──► Validator D ─┤  2. exec_prompt → verdict token
      └──► Validator E ─┘  3. exec_prompt → reasoning JSON
                    │
                    ▼
         prompt_comparative judges
         combined {token, reasoning_raw}
                    │
                    ▼
          Verdict stored on-chain
                    │
                    ▼
       Mirrored to Supabase (display only)
                    │
                    ▼
        Farmer sees Consensus Verdict Terminal
```

---

## Security & Trust Model

- **Row Level Security (RLS)** enforced at the database level — users can only read and write their own farms, cases, and evidence
- **Evidence manifest endpoint** uses the service-role key server-side so GenLayer validators (unauthenticated) can read evidence without bypassing user-level RLS for any other data
- **Verdicts are on-chain** — Supabase cannot be edited to change a verdict; the contract is the source of truth
- **Embedded wallet keys** are generated client-side during onboarding. The platform never stores raw private keys — only an encrypted wrap, decrypted at signing time with the user's password
- **Evidence integrity** — each document's SHA-256 is included in the manifest; validators can verify file integrity against the hash stored on-chain in the evidence digest

---

## Contract Reference

**File:** `contract/agrosense_advisory.py`  
**Version:** v0.2.17  
**Network:** GenLayer StudioNet  
**Address:** `0x79d68980436D96Ee489C3b1786A739E2EE41BC73`

| Method | Type | Description |
|---|---|---|
| `submit_advisory(advisory_id, farm_region, crop_type, advisory_question, planting_window, weather_context, market_context, weather_url, market_url, soil_evidence_hash, evidence_manifest_url, user_observation_text, backend_proposed_plan_a, backend_proposed_plan_b, backend_proposed_plan_c)` | write | Fetch evidence, run validator consensus, store verdict |
| `get_verdict(advisory_id)` | view | Return the finalised verdict JSON for a case |
| `get_submitter(advisory_id)` | view | Return the wallet address that submitted a case |
