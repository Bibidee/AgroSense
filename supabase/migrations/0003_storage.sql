-- Evidence bucket (private). Path layout: {user_id}/{advisory_case_id}/{filename}
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
