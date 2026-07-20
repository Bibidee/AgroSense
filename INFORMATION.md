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
Up to 3 evidence files (soil reports, photos, lab results) can be attached to the case before submission.

### 3. GenLayer Adjudication (Two-Stage Consensus)

The `AgroSenseAdvisory` Intelligent Contract runs on GenLayer StudioNet:

**Stage 1 — Action token (strict consensus)**  
Every validator independently selects one of six canonical verdicts:

| Token | Meaning |
|---|---|
| `plant_now` | Conditions are favourable — proceed |
| `delay_planting` | Wait before planting |
| `irrigate_first` | Irrigate before any other action |
| `proceed_with_caution` | Action is viable but risks exist |
| `avoid_action` | Do not take the proposed action |
| `request_more_evidence` | Insufficient data to advise |

All validators must agree on the same token (`strict_eq`). If they don't converge, the system returns `request_more_evidence`.

**Stage 2 — Reasoning + risk + confidence (relaxed consensus)**  
Using the agreed token as an anchor, validators produce a JSON object containing:
- `risk_level` — low / moderate / high
- `confidence` — weak / moderate / strong
- `selected_plan` — which of three backend-proposed plans (A, B, C) best fits
- `reasoning` — 1–2 sentence justification

Validators may word their reasoning differently; substantive disagreement on the action is not allowed (`prompt_comparative`).

### 4. Verdict Display
The finalised verdict is stored on-chain and mirrored to Supabase for fast UI reads. The dashboard shows a rotating feed of recent verdicts across all farms.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js 15 (App Router, Server Actions) |
| Database & Auth | Supabase (Postgres + Row Level Security + Storage) |
| On-chain AI | GenLayer StudioNet |
| Intelligent Contract | Python (`genlayer` SDK) |
| Deployment | Vercel |

---

## Key Pages

| Route | Purpose |
|---|---|
| `/dashboard` | Farm overview and recent verdict feed |
| `/farms` | Register and manage farms |
| `/cases` | All advisory cases |
| `/cases/new` | Advisory Packet Builder — case + weather + evidence |
| `/cases/[id]` | Case detail with live verdict polling |
| `/verdicts/[id]` | Full verdict breakdown |
| `/evidence` | Evidence file management |
| `/onboarding` | New user setup + wallet creation |
| `/profile` | Wallet + encrypted key export |
| `/settings` | Notification preferences + data export |
| `/admin` | Admin case management |

---

## Data Flow Diagram

```
Farmer (browser)
      │
      ▼
Next.js Server Action
      │  builds advisory packet
      ▼
GenLayer StudioNet ──► Validator A ─┐
                   ──► Validator B ─┼──► Strict consensus on token
                   ──► Validator C ─┘
                                    │
                                    ▼
                        Relaxed consensus on reasoning
                                    │
                                    ▼
                         Verdict stored on-chain
                                    │
                                    ▼
                     Supabase mirror (display only)
                                    │
                                    ▼
                         Farmer sees verdict in UI
```

---

## Security & Trust Model

- **Row Level Security (RLS)** is enforced at the database level — users can only read and write their own farms, cases, and evidence.
- **Verdicts are on-chain** — Supabase cannot be edited to change a verdict; the contract is the source of truth.
- **Wallet keys** are generated client-side during onboarding and can be exported in encrypted form. The platform never stores raw private keys.
- **Evidence hashes** are included in the on-chain submission so the validator network can verify that the evidence submitted matches what the farmer uploaded.

---

## Contract Reference

**File:** `contract/agrosense_advisory.py`  
**Deployed on:** GenLayer StudioNet  

Public methods:

| Method | Type | Description |
|---|---|---|
| `submit_advisory(...)` | write | Submit a case for consensus adjudication |
| `get_verdict(advisory_id)` | view | Read a finalised verdict |
| `get_submitter(advisory_id)` | view | Read the submitter's address |
