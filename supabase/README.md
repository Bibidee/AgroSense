# Supabase

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
