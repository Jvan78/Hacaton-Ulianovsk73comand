CREATE TABLE IF NOT EXISTS import_jobs (
  id serial PRIMARY KEY,
  file_url text,
  user_login text,
  status text DEFAULT 'pending', -- pending, running, success, failed
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  error text,
  file_hash text
);
