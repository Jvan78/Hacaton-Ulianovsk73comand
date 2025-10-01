WITH to_update AS (
  SELECT id
  FROM flights
  WHERE start_geom IS NOT NULL AND start_region_id IS NULL
  LIMIT 1000
)
UPDATE flights f
SET start_region_id = sub.gid
FROM (
  SELECT t.id, r.gid
  FROM to_update t
  JOIN LATERAL (
    SELECT gid FROM public.regions ORDER BY geom <-> (SELECT geom FROM flights WHERE id = t.id) LIMIT 1
  ) r ON true
) sub
WHERE f.id = sub.id;
