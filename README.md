# AgroSense

Consensus backed farm intelligence. GenLayer powered advisory verdicts.

## Stack
Next.js 15 (App Router) · Supabase (Auth + Postgres + Storage) · GenLayer StudioNet · Vercel

## Local dev
```bash
cp .env.example .env.local   # fill values
npm install
npm run dev
```

## Stages
1. **Scaffold** — this stage. Next.js skeleton + design tokens.
2. Supabase schema + RLS + Storage.
3. Auth + embedded wallet + recovery key.
4. Farms + advisory cases + evidence upload.
5. GenLayer `AgroSenseAdvisory` Intelligent Contract → deploy on StudioNet.
6. Verdict UI + admin + profile/wallet + settings.
7. Vercel deploy.

GenLayer is the source of truth for advisory verdicts. Supabase mirrors the on-chain result for product display only.
