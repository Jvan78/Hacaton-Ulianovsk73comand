# data/reparse_and_fill.py
import json
import math
from typing import Any, List, Tuple, Optional
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
import traceback

DSN = "host=host.docker.internal dbname=gis user=postgres password=postgres port=5432"
BATCH = 500
ERROR_LOG = os.path.join(os.path.dirname(__file__), "reparse_errors.log")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
try:
    from app.parser import normalize_row
except Exception:
    try:
        from parser import normalize_row
    except Exception as e:
        print("Не удалось импортировать normalize_row из parser. Проверь путь. Ошибка:", e)
        raise

def as_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return v
    if isinstance(v, int):
        return float(v)
    s = str(v).strip()
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return float(s)
    except Exception:
        return None

def as_text_or_none(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None

def log_error(msg: str):
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def process_batch(rows: List[Tuple[int, str]]) -> int:
    updates = []
    for id_, raw_text in rows:
        try:
            if not raw_text:
                raw_obj = {}
            else:
                raw_obj = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
                if not isinstance(raw_obj, dict):
                    raw_obj = {}
        except Exception as e:
            log_error(f"[PARSE_JSON_ERROR] id={id_} err={e} snippet={str(raw_text)[:300]}")
            raw_obj = {}

        sample_row = {
            'SHR': raw_obj.get('SHR') if isinstance(raw_obj, dict) else None,
            'DEP': raw_obj.get('DEP') if isinstance(raw_obj, dict) else None,
            'ARR': raw_obj.get('ARR') if isinstance(raw_obj, dict) else None,
            'center': raw_obj.get('center') if isinstance(raw_obj, dict) else None
        }

        try:
            parsed = normalize_row(sample_row) or {}
        except Exception as e:
            msg = f"[NORMALIZE_ERROR] id={id_} err={e} row_snippet={str(sample_row)[:400]}"
            print(msg)
            log_error(msg)
            log_error(traceback.format_exc())
            parsed = {}

        start_lat = as_float(parsed.get('start_lat'))
        start_lon = as_float(parsed.get('start_lon'))
        end_lat = as_float(parsed.get('end_lat'))
        end_lon = as_float(parsed.get('end_lon'))
        start_time = as_text_or_none(parsed.get('start_time'))
        end_time = as_text_or_none(parsed.get('end_time'))
        fingerprint = as_text_or_none(parsed.get('fingerprint'))

        updates.append((start_lat, start_lon, end_lat, end_lon, start_time, end_time, fingerprint, id_))

    if not updates:
        return 0

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor()
        # ВАЖНО: здесь мы записываем fingerprint только если в таблице flights
        # ещё нет строки с таким fingerprint. Иначе оставляем старый fingerprint.
        sql = """
        WITH v(start_lat, start_lon, end_lat, end_lon, start_time, end_time, fingerprint, id) AS (VALUES %s)
        UPDATE flights f
        SET
          start_lat = COALESCE(NULLIF(v.start_lat, '')::double precision, f.start_lat),
          start_lon = COALESCE(NULLIF(v.start_lon, '')::double precision, f.start_lon),
          end_lat = COALESCE(NULLIF(v.end_lat, '')::double precision, f.end_lat),
          end_lon = COALESCE(NULLIF(v.end_lon, '')::double precision, f.end_lon),
          start_time = COALESCE(NULLIF(v.start_time, '')::timestamptz, f.start_time),
          end_time = COALESCE(NULLIF(v.end_time, '')::timestamptz, f.end_time),
          fingerprint = CASE
                          WHEN v.fingerprint IS NULL THEN f.fingerprint
                          WHEN NOT EXISTS (SELECT 1 FROM flights f2 WHERE f2.fingerprint = v.fingerprint) THEN v.fingerprint
                          ELSE f.fingerprint
                        END,
          start_geom = CASE
                         WHEN v.start_lat IS NOT NULL AND v.start_lon IS NOT NULL
                         THEN ST_SetSRID(ST_MakePoint((v.start_lon)::double precision, (v.start_lat)::double precision), 4326)
                         ELSE f.start_geom
                       END,
          end_geom = CASE
                       WHEN v.end_lat IS NOT NULL AND v.end_lon IS NOT NULL
                       THEN ST_SetSRID(ST_MakePoint((v.end_lon)::double precision, (v.end_lat)::double precision), 4326)
                       ELSE f.end_geom
                     END
        FROM v
        WHERE f.id = v.id;
        """
        execute_values(cur, sql, updates, template="(%s,%s,%s,%s,%s,%s,%s,%s)")
        conn.commit()
        return len(updates)
    except Exception as e:
        if conn:
            conn.rollback()
        msg = f"[ERROR] process_batch failed: {e}"
        print(msg)
        log_error(msg)
        log_error(traceback.format_exc())
        return 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def stream_rows_and_update():
    conn = None
    cur = None
    total_updated = 0
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor(name='cur_missing')
        cur.execute("SELECT id, raw_payload::text FROM flights WHERE start_geom IS NULL OR end_geom IS NULL;")
        batch = []
        for row in cur:
            batch.append(row)
            if len(batch) >= BATCH:
                n = process_batch(batch)
                total_updated += n
                print(f"[INFO] Updated {total_updated} rows so far")
                batch = []
        if batch:
            n = process_batch(batch)
            total_updated += n
        print("[DONE] total updated:", total_updated)
    except Exception as e:
        print("[ERROR] stream_rows_and_update:", e)
        log_error("[ERROR] stream_rows_and_update: " + str(e) + "\n" + traceback.format_exc())
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Start reparse_and_fill.py — BATCH =", BATCH)
    stream_rows_and_update()
