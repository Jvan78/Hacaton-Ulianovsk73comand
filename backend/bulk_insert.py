import psycopg2
from psycopg2.extras import execute_values
import json, os

DB_DSN = os.getenv("DB_DSN", "host=localhost dbname=gis user=postgres password=postgres")

def bulk_insert(items):
    # items: list of dicts with keys: flight_id, uav_type, start_time, end_time, duration_seconds, start_lat, start_lon, end_lat, end_lon, raw_payload, fingerprint
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    rows = []
    for it in items:
        rows.append((
            it.get('flight_id'),
            it.get('uav_type'),
            it.get('start_time'),
            it.get('end_time'),
            it.get('duration_seconds'),
            None if it.get('start_lon') is None or it.get('start_lat') is None else f"SRID=4326;POINT({it.get('start_lon')} {it.get('start_lat')})",
            None if it.get('end_lon') is None or it.get('end_lat') is None else f"SRID=4326;POINT({it.get('end_lon')} {it.get('end_lat')})",
            json.dumps(it.get('raw_payload') or {}),
            it.get('fingerprint'),
            it.get('start_lat'),
            it.get('start_lon'),
            it.get('end_lat'),
            it.get('end_lon'),
        ))
    sql = """
    INSERT INTO flights (flight_id, uav_type, start_time, end_time, duration_seconds, start_geom, end_geom, raw_payload, fingerprint, start_lat, start_lon, end_lat, end_lon)
    VALUES %s
    ON CONFLICT (fingerprint) DO NOTHING
    """
    # execute_values with template to handle geom using ST_GeomFromText
    template = "(%s,%s,%s,%s,%s,ST_GeomFromEWKT(%s),ST_GeomFromEWKT(%s),%s,%s,%s,%s,%s,%s)"
    execute_values(cur, sql, rows, template=template)
    conn.commit()
    cur.close()
    conn.close()
