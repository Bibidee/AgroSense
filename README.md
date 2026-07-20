# AgroSense

Consensus-backed farm intelligence. GenLayer-powered advisory verdicts.

**Live:** [the-agrosense.vercel.app](https://the-agrosense.vercel.app)

## What it does

Farmers create advisory cases (pest outbreaks, disease diagnoses, input recommendations, etc.), upload evidence, and receive verdicts from an on-chain AI advisory contract deployed on GenLayer StudioNet. Multiple AI validators reach consensus before a verdict is finalised — no single model decides alone.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router) |
| Auth & DB | Supabase (Auth + Postgres + Storage) |
| On-chain AI | GenLayer StudioNet — `AgroSenseAdvisory` Intelligent Contract |
| Deployment | Vercel |

## Features

- **Farms** — register and manage farm profiles
- **Advisory cases** — create cases with weather data auto-pull and evidence uploads
- **Evidence** — attach images and documents to cases
- **GenLayer verdicts** — on-chain consensus verdict with live polling until finalised
- **Dashboard** — overview of recent verdicts and farm activity
- **Onboarding** — guided setup for new users (wallet generation + recovery key export)
- **Profile & wallet** — embedded wallet with encrypted key export
- **Settings** — notification preferences and data export
- **Admin** — case management panel

## Local dev

```bash
cp .env.example .env.local   # fill in Supabase + GenLayer values
npm install
npm run dev
```

## Project structure

```
app/                   # Next.js App Router pages
  dashboard/           # Post-login overview
  farms/               # Farm management
  cases/               # Advisory cases + verdict polling
  cases/new/           # Case creation with weather pull
  evidence/            # Evidence uploads
  verdicts/[id]/       # Verdict detail
  onboarding/          # New user setup
  profile/             # Wallet + key export
  settings/            # Notifications + data export
  admin/               # Admin panel
contract/
  agrosense_advisory.py  # GenLayer Intelligent Contract
supabase/
  migrations/          # Schema, RLS, storage, grants, settings
```

## How verdicts work

1. A farmer submits a case with evidence.
2. The `AgroSenseAdvisory` Intelligent Contract is invoked on GenLayer StudioNet.
3. Multiple AI validator nodes independently reason about the case and reach consensus.
4. The finalised verdict is written on-chain; Supabase mirrors it for display only.

> GenLayer is the source of truth for advisory verdicts. Supabase stores a read-only mirror.
