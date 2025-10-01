-- 1) Создаем staging таблицу, если еще нет
CREATE TABLE IF NOT EXISTS staging_raw (
    raw jsonb
);

-- 2) Очищаем staging
TRUNCATE staging_raw;

-- 3) ВНИМАНИЕ: для psycopg2 НЕ использовать \COPY.
-- Если хочешь вставить файл напрямую, делай это через Python (import_from_upload),
-- либо через psql:
--   docker compose exec db psql -U postgres -d gis -c "\COPY staging_raw(raw) FROM '/data/parsed.ndjson';"

-- 4) Вставка в flights с игнорированием дубликатов flight_id + start_time
INSERT INTO flights (
    flight_id,
    uav_type,
    start_time,
    end_time,
    duration_seconds,
    start_geom,
    end_geom,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    fingerprint,
    raw_payload
)
SELECT
    (raw->>'flight_id')::text AS flight_id,
    (raw->>'uav_type')::text AS uav_type,
    CASE WHEN raw->>'start_time' IS NOT NULL THEN (raw->>'start_time')::timestamptz ELSE NULL END AS start_time,
    CASE WHEN raw->>'end_time' IS NOT NULL THEN (raw->>'end_time')::timestamptz ELSE NULL END AS end_time,
    CASE WHEN raw->>'duration_seconds' IS NOT NULL THEN (raw->>'duration_seconds')::int ELSE NULL END AS duration_seconds,
    CASE WHEN raw->>'start_lon' IS NOT NULL AND raw->>'start_lat' IS NOT NULL
         THEN ST_SetSRID(ST_Point((raw->>'start_lon')::double precision, (raw->>'start_lat')::double precision),4326)
         ELSE NULL END AS start_geom,
    CASE WHEN raw->>'end_lon' IS NOT NULL AND raw->>'end_lat' IS NOT NULL
         THEN ST_SetSRID(ST_Point((raw->>'end_lon')::double precision, (raw->>'end_lat')::double precision),4326)
         ELSE NULL END AS end_geom,
    CASE WHEN raw->>'start_lat' IS NOT NULL THEN (raw->>'start_lat')::double precision ELSE NULL END AS start_lat,
    CASE WHEN raw->>'start_lon' IS NOT NULL THEN (raw->>'start_lon')::double precision ELSE NULL END AS start_lon,
    CASE WHEN raw->>'end_lat' IS NOT NULL THEN (raw->>'end_lat')::double precision ELSE NULL END AS end_lat,
    CASE WHEN raw->>'end_lon' IS NOT NULL THEN (raw->>'end_lon')::double precision ELSE NULL END AS end_lon,
    (raw->>'fingerprint')::text AS fingerprint,
    raw AS raw_payload
FROM staging_raw
ON CONFLICT (flight_id, start_time) DO NOTHING;

-- 5) Обновляем геометрию для записей, где она не сформировалась
UPDATE flights
SET start_geom = ST_SetSRID(ST_Point(start_lon, start_lat),4326)
WHERE start_geom IS NULL AND start_lat IS NOT NULL AND start_lon IS NOT NULL;

UPDATE flights
SET end_geom = ST_SetSRID(ST_Point(end_lon, end_lat),4326)
WHERE end_geom IS NULL AND end_lat IS NOT NULL AND end_lon IS NOT NULL;

-- 6) Привязка к регионам через ST_Within
UPDATE flights f
SET start_region_id = r.gid
FROM regions r
WHERE f.start_region_id IS NULL
  AND f.start_geom IS NOT NULL
  AND ST_Intersects(r.geom, f.start_geom);

UPDATE flights f
SET end_region_id = r.gid
FROM regions r
WHERE f.end_region_id IS NULL
  AND f.end_geom IS NOT NULL
  AND ST_Intersects(r.geom, f.end_geom);

-- 7) Быстрая проверка
SELECT COUNT(*) AS total_flights FROM flights;
SELECT COUNT(*) AS with_start_geom FROM flights WHERE start_geom IS NOT NULL;
SELECT COUNT(*) AS with_end_geom FROM flights WHERE end_geom IS NOT NULL;
SELECT COUNT(*) AS with_start_region FROM flights WHERE start_region_id IS NOT NULL;
SELECT COUNT(*) AS with_end_region FROM flights WHERE end_region_id IS NOT NULL;
