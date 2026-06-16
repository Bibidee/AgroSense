-- Notification preferences + onboarding gate column tweaks.
alter table public.profiles
  add column if not exists notification_prefs jsonb not null default
    '{"verdict_email":true,"risk_email":true,"weekly_digest":false}'::jsonb;
