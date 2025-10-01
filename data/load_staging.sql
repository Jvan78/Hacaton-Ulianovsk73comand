TRUNCATE staging_raw;
\COPY staging_raw(raw) FROM '/data/parsed.ndjson';
