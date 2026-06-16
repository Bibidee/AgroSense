-- Enable RLS and create policies. auth.uid() must equal user_id.

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
