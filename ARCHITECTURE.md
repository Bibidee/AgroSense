# AgroSense — Architecture

## Source of truth
GenLayer is authoritative for advisory verdicts. Next.js prepares the case,
Supabase stores product state and a mirror of the contract result.

```
[ Next.js (Vercel) ] -- prepare packet --> [ GenLayer StudioNet contract ]
        |                                          |
        +--- store state & mirror ---> [ Supabase Postgres + Storage ]
                                                   |
                                                   +-- Auth (email/password)
```

## Wallet model (embedded, non-rotating)
1. On signup: generate secp256k1 EOA → encrypt privkey under random WEK (AES-GCM).
2. Wrap the WEK twice:
   - **password wrap** = AES-GCM(WEK) under PBKDF2(password, saltP).
   - **recovery wrap** = AES-GCM(WEK) under PBKDF2(recoveryKey, saltR).
3. Address never changes. Password reset = re-wrap existing WEK under new
   password using the recovery-wrap path. Private key export requires
   password re-auth and is audit logged.

## RLS
Every user-owned table enforces `auth.uid() = user_id` or admin. Storage
objects in `evidence` are pathed `{user_id}/{case_id}/...` and policies pin
on the first folder segment.

## Why GenLayer is necessary
The contract does not output deterministic thresholds. It invokes
`gl.nondet.exec_prompt` over three competing plans (A/B/C) and converges via
`gl.eq_principle_strict_eq` on a canonical action token. Different LLM
wordings collapse to the same agreed verdict. This is meaningful
non-determinism: the answer requires interpretation, comparison, and
judgment from independent validators.
