"""
Stage 2 - Supabase: schema, RLS, storage, seed.
Run:  python scripts/stage2_supabase.py
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F: dict[str, str] = {}

F["supabase/config.toml"] = r"""project_id = "agrosense"
[api]
port = 54321
schemas = ["public", "storage"]
[db]
port = 54322
[studio]
port = 54323
[auth]
enable_signup = true
enable_confirmations = false
"""

# ---------- 0001 schema ----------
F["supabase/migrations/0001_schema.sql"] = r"""-- AgroSense core schema
create extension if not exists "pgcrypto";

-- ---------- profiles ----------
create table public.profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  role text not null default 'user' check (role in ('user','admin')),
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index profiles_user_id_idx on public.profiles(user_id);

-- ---------- wallets ----------
create table public.wallets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  address text not null unique,
  -- AES-GCM(privkey) keyed by the Wallet Encryption Key (WEK)
  encrypted_private_key text not null,        -- base64: iv || ciphertext || tag
  encryption_version int  not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index wallets_user_id_idx on public.wallets(user_id);

-- ---------- wallet_key_wraps ----------
-- Two rows per wallet: method='password' and method='recovery'.
-- Each row stores AES-GCM(WEK) keyed by PBKDF2(secret, salt).
create table public.wallet_key_wraps (
  id uuid primary key default gen_random_uuid(),
  wallet_id uuid not null references public.wallets(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  method text not null check (method in ('password','recovery')),
  encrypted_wallet_key text not null,         -- base64 iv||ct||tag
  salt text not null,                         -- base64
  kdf_params jsonb not null default '{"algo":"PBKDF2-SHA256","iter":210000,"keylen":32}'::jsonb,
  created_at timestamptz not null default now(),
  unique (wallet_id, method)
);

-- ---------- farms ----------
create table public.farms (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  country text not null,
  region text,
  latitude numeric,
  longitude numeric,
  nearest_town text,
  farm_size numeric,
  soil_type text,
  irrigation_available boolean not null default false,
  main_crops text[] not null default '{}',
  previous_planting_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index farms_user_id_idx on public.farms(user_id);

-- ---------- advisory_cases ----------
create type public.advisory_status as enum (
  'draft','evidence_added','ready','submitted','consensus_pending',
  'verdict_issued','needs_more_evidence','archived'
);
create type public.decision_type as enum (
  'plant_now','delay_planting','irrigate','harvest_window','risk_check'
);

create table public.advisory_cases (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  farm_id uuid not null references public.farms(id) on delete cascade,
  crop_type text not null,
  advisory_question text not null,
  decision_type public.decision_type not null,
  planting_window text,
  user_observation text,
  proposed_plan_a text not null default 'Plant now',
  proposed_plan_b text not null default 'Delay planting',
  proposed_plan_c text not null default 'Irrigate first',
  status public.advisory_status not null default 'draft',
  submitted_to_genlayer_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index advisory_cases_user_id_idx on public.advisory_cases(user_id);
create index advisory_cases_farm_id_idx on public.advisory_cases(farm_id);

-- ---------- evidence_files ----------
create table public.evidence_files (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  advisory_case_id uuid not null references public.advisory_cases(id) on delete cascade,
  file_url text not null,
  file_path text not null,
  file_bucket text not null default 'evidence',
  file_type text not null,
  file_size int not null,
  evidence_hash text not null,
  uploaded_by uuid references auth.users(id),
  created_at timestamptz not null default now()
);
create index evidence_files_case_idx on public.evidence_files(advisory_case_id);

-- ---------- data_snapshots ----------
create table public.data_snapshots (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  advisory_case_id uuid not null references public.advisory_cases(id) on delete cascade,
  source_type text not null check (source_type in ('weather','market','soil','manual')),
  source_url text,
  snapshot_json jsonb not null,
  snapshot_hash text not null,
  created_at timestamptz not null default now()
);

-- ---------- genlayer_verdicts (mirror) ----------
create table public.genlayer_verdicts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  advisory_case_id uuid not null references public.advisory_cases(id) on delete cascade,
  contract_address text not null,
  transaction_hash text not null,
  advisory_id_on_chain text not null,
  verdict text not null,
  risk_level text not null,
  confidence_label text not null,
  selected_plan text not null,
  reasoning_summary text,
  evidence_digest text not null,
  consensus_status text not null,
  consensus_timestamp timestamptz,
  created_at timestamptz not null default now()
);
create index genlayer_verdicts_case_idx on public.genlayer_verdicts(advisory_case_id);

-- ---------- recovery_audit_logs ----------
create table public.recovery_audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  wallet_id uuid references public.wallets(id) on delete cascade,
  action text not null,         -- 'recovery_used','password_rewrap','privkey_exported','recovery_key_rotated'
  ip_address text,
  user_agent text,
  created_at timestamptz not null default now()
);

-- ---------- admin_review_notes ----------
create table public.admin_review_notes (
  id uuid primary key default gen_random_uuid(),
  advisory_case_id uuid not null references public.advisory_cases(id) on delete cascade,
  admin_user_id uuid not null references auth.users(id) on delete cascade,
  note text not null,
  created_at timestamptz not null default now()
);

-- ---------- contract_activity_logs ----------
create table public.contract_activity_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  advisory_case_id uuid references public.advisory_cases(id) on delete cascade,
  contract_address text not null,
  transaction_hash text,
  action text not null,
  status text not null,
  error_message text,
  created_at timestamptz not null default now()
);

-- ---------- updated_at trigger ----------
create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

create trigger t_profiles_upd before update on public.profiles
  for each row execute function public.touch_updated_at();
create trigger t_wallets_upd before update on public.wallets
  for each row execute function public.touch_updated_at();
create trigger t_farms_upd before update on public.farms
  for each row execute function public.touch_updated_at();
create trigger t_cases_upd before update on public.advisory_cases
  for each row execute function public.touch_updated_at();

-- ---------- admin helper ----------
create or replace function public.is_admin(uid uuid) returns boolean
language sql stable as $$
  select exists (select 1 from public.profiles where user_id = uid and role = 'admin');
$$;
"""

# ---------- 0002 RLS ----------
F["supabase/migrations/0002_rls.sql"] = r"""-- Enable RLS and create policies. auth.uid() must equal user_id.

alter table public.profiles               enable row level security;
alter table public.wallets                enable row level security;
alter table public.wallet_key_wraps       enable row level security;
alter table public.farms                  enable row level security;
alter table public.advisory_cases         enable row level security;
alter table public.evidence_files         enable row level security;
alter table public.data_snapshots         enable row level security;
alter table public.genlayer_verdicts      enable row level security;
alter table public.recovery_audit_logs    enable row level security;
alter table public.admin_review_notes     enable row level security;
alter table public.contract_activity_logs enable row level security;

-- profiles: user reads own + admin reads all
create policy profiles_self_select on public.profiles
  for select using (auth.uid() = user_id or public.is_admin(auth.uid()));
create policy profiles_self_insert on public.profiles
  for insert with check (auth.uid() = user_id);
create policy profiles_self_update on public.profiles
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- wallets / wraps: user-only. Privileged writes go through service role.
create policy wallets_self_select on public.wallets
  for select using (auth.uid() = user_id);
create policy wallet_wraps_self_select on public.wallet_key_wraps
  for select using (auth.uid() = user_id);

-- farms
create policy farms_owner_all on public.farms
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- advisory_cases
create policy cases_owner_all on public.advisory_cases
  for all using (auth.uid() = user_id or public.is_admin(auth.uid()))
  with check (auth.uid() = user_id);

-- evidence_files
create policy evidence_owner_all on public.evidence_files
  for all using (auth.uid() = user_id or public.is_admin(auth.uid()))
  with check (auth.uid() = user_id);

-- data_snapshots
create policy snapshots_owner_all on public.data_snapshots
  for all using (auth.uid() = user_id or public.is_admin(auth.uid()))
  with check (auth.uid() = user_id);

-- verdicts (insert by service role only; read by owner + admin)
create policy verdicts_owner_select on public.genlayer_verdicts
  for select using (auth.uid() = user_id or public.is_admin(auth.uid()));

-- recovery audit (insert by service role; read by owner)
create policy recovery_audit_self_select on public.recovery_audit_logs
  for select using (auth.uid() = user_id);

-- admin review notes (admin only)
create policy admin_notes_admin_all on public.admin_review_notes
  for all using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));

-- contract activity logs (read by owner + admin)
create policy contract_logs_owner_select on public.contract_activity_logs
  for select using (auth.uid() = user_id or public.is_admin(auth.uid()));

-- Auto-create profile on auth signup
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (user_id, email)
  values (new.id, new.email)
  on conflict (user_id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
"""

# ---------- 0003 storage ----------
F["supabase/migrations/0003_storage.sql"] = r"""-- Evidence bucket (private). Path layout: {user_id}/{advisory_case_id}/{filename}
insert into storage.buckets (id, name, public)
values ('evidence','evidence', false)
on conflict (id) do nothing;

-- Owner can read/write only their own folder.
create policy "evidence read own" on storage.objects
  for select using (
    bucket_id = 'evidence' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "evidence insert own" on storage.objects
  for insert with check (
    bucket_id = 'evidence' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "evidence update own" on storage.objects
  for update using (
    bucket_id = 'evidence' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "evidence delete own" on storage.objects
  for delete using (
    bucket_id = 'evidence' and (storage.foldername(name))[1] = auth.uid()::text
  );
"""

F["supabase/seed.sql"] = r"""-- Optional seed (run after creating an auth user via dashboard or app).
-- Promote a user to admin:
--   update public.profiles set role='admin' where email='you@example.com';
"""

F["supabase/README.md"] = r"""# Supabase

## Apply migrations to your Supabase project
Option A — Supabase CLI (recommended):
```bash
supabase login
supabase link --project-ref <your-project-ref>
supabase db push
```

Option B — paste each SQL file into the Supabase SQL editor in order:
1. `migrations/0001_schema.sql`
2. `migrations/0002_rls.sql`
3. `migrations/0003_storage.sql`

## Storage bucket
`evidence` bucket is private. Files are written under `{user_id}/{advisory_case_id}/{filename}`.

## Promote an admin
```sql
update public.profiles set role='admin' where email='you@example.com';
```
"""

def main() -> None:
    n = 0
    for rel, body in F.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        n += 1
    print(f"[stage2] wrote {n} files")

if __name__ == "__main__":
    main()
