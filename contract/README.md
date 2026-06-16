# AgroSenseAdvisory — GenLayer Intelligent Contract

This contract is the **source of truth** for AgroSense advisory verdicts.

## Why GenLayer (not deterministic)
- Three competing plans (A/B/C) are sent in with the case.
- The contract invokes `gl.nondet.exec_prompt(...)` so every validator runs
  the LLM independently against the same prompt + evidence.
- `gl.eq_principle_strict_eq(...)` produces consensus on a structured
  canonical verdict token — different wordings collapse to the same agreed
  action (`plant_now`, `delay_planting`, etc.).
- The contract stores only the small agreed result; large evidence stays in
  Supabase Storage and is referenced by hash.

## Deploy to StudioNet (no Docker)
1. Open GenLayer Studio: https://studio.genlayer.com
2. Connect StudioNet and ensure your account has GEN test tokens.
3. Create a new contract → paste the contents of `agrosense_advisory.py`.
4. Compile, then deploy. Copy the deployed contract address.
5. Set it in your project `.env.local`:
   ```
   NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS=0x...
   GENLAYER_SUBMITTER_PRIVATE_KEY=0x...    # StudioNet test key with GEN
   ```
6. Restart `npm run dev`.

## Verifying GenLayer is doing the judgment
- Submit a case from the UI.
- Observe transaction in Studio: multiple validators evaluate the prompt,
  then converge via the equivalence principle.
- The on-chain stored verdict matches the verdict mirrored into Supabase.

> Verify exact decorator/API names against the latest
> https://docs.genlayer.com/ and https://skills.genlayer.com/ — pin the
> `genlayer-py-std` version that matches StudioNet.
