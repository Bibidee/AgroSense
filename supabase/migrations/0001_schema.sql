-- AgroSense core schema
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
