-- Store the original file name and extracted text alongside each evidence file.
-- extracted_text is populated server-side at upload time for PDF files;
-- null for images / JSON since validators can't read binary.
alter table public.evidence_files
  add column if not exists file_name text,
  add column if not exists extracted_text text;
