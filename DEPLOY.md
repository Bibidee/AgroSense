# AgroSense — Deployment

## 1. Supabase
- Create a Supabase project.
- Apply migrations (`supabase db push` or paste each `supabase/migrations/*.sql`).
- Set Auth → Email/Password ON, confirmations OFF (or wire confirm flow).
- Storage bucket `evidence` is created by migration 0003.
- Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` in your env.

## 2. Wallet KDF pepper
Generate a 32-byte base64 secret used to namespace key derivation:
```bash
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
```
Set as `WALLET_KDF_PEPPER` (server only). Rotating this invalidates existing wraps.

## 3. GenLayer
- `AgroSenseAdvisory` is deployed on StudioNet at:
  **`0x42F6b64A948BbB2E9eBD57919e07fB286A6D291F`**
- This address is hard-wired in [`lib/genlayer/contract.ts`](lib/genlayer/contract.ts)
  and pre-filled in `.env.local` / `.env.example`. To redeploy, update both.
- Still required: `GENLAYER_RPC_URL`, `GENLAYER_SUBMITTER_PRIVATE_KEY`.

## 4. Vercel
```bash
npm i -g vercel
vercel link
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env add WALLET_KDF_PEPPER
vercel env add NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS
vercel env add GENLAYER_RPC_URL
vercel env add GENLAYER_SUBMITTER_PRIVATE_KEY
vercel env add NEXT_PUBLIC_APP_URL
vercel --prod
```

## 5. Promote an admin
In Supabase SQL editor:
```sql
update public.profiles set role='admin' where email='you@example.com';
```
