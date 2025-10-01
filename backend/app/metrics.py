# metrics.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import psycopg2
import os
import time

router = APIRouter(prefix="/api/v1/metrics")

DB_DSN = os.getenv("DB_DSN", "host=localhost dbname=gis user=postgres password=postgres")

# Простое in-memory cache with TTL
_cache = {}
_CACHE_TTL = 30  # seconds

def _get_cached(key):
    rec = _cache.get(key)
    if not rec:
        return None
    ts, val = rec
    if time.time() - ts > _CACHE_TTL:
        del _cache[key]
        return None
    return val

def _set_cache(key, val):
    _cache[key] = (time.time(), val)

@router.get("/regions")
def metrics_regions(from_dt: str = Query(None), to_dt: str = Query(None), top: int = Query(10)):
    """
    from_dt / to_dt expected as ISO strings, e.g. 2025-09-01T00:00:00Z
    """
    cache_key = f"regions:{from_dt}:{to_dt}:{top}"
    cached = _get_cached(cache_key)
    if cached:
        return JSONResponse(cached)

    # build SQL (safe paramization via psycopg2)
    sql = """
    SELECT r.name, COUNT(*) AS cnt
    FROM flights f
    JOIN public.regions r ON f.start_region_id = r.id
    WHERE f.start_region_id IS NOT NULL
    """
    params = []
    if from_dt:
        sql += " AND f.start_time >= %s"
        params.append(from_dt)
    if to_dt:
        sql += " AND f.start_time <= %s"
        params.append(to_dt)
    sql += " GROUP BY r.id, r.name ORDER BY cnt DESC LIMIT %s;"
    params.append(top)

    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    res = [{"region": r[0], "count": int(r[1])} for r in rows]
    _set_cache(cache_key, res)
    return JSONResponse(res)
