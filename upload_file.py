# upload_file_json.py
import json
import psycopg2
from psycopg2.extras import execute_batch
import os
import sys

# ---------- НАСТРОЙКИ (отредактируй при необходимости) ----------
DB_HOST = "localhost"      # если запускаешь из Windows -> localhost; если внутри контейнера -> "db"
DB_PORT = 5432
DB_NAME = "gis"
DB_USER = "postgres"
DB_PASS = "postgres"

TABLE_NAME = "flights_import"
FILE_PATH = os.path.join("data", "parsed_normalized.ndjson")  # путь к файлу
BATCH_SIZE = 1000  # количество записей за одну батч-вставку
# -----------------------------------------------------------------

if not os.path.exists(FILE_PATH):
    print(f"Файл не найден: {FILE_PATH}", file=sys.stderr)
    sys.exit(1)

def normalize_value(v):
    # Приводим пустые строки к None, оставляем числа/строки как есть
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
)
cur = conn.cursor()

insert_sql = f"""
INSERT INTO {TABLE_NAME} (
  flight_id, uav_type, start_time, end_time, duration_seconds,
  start_lat, start_lon, end_lat, end_lon, time_token,
  raw_payload, fingerprint
) VALUES (
  %(flight_id)s, %(uav_type)s, %(start_time)s, %(end_time)s, %(duration_seconds)s,
  %(start_lat)s, %(start_lon)s, %(end_lat)s, %(end_lon)s, %(time_token)s,
  %(raw_payload)s, %(fingerprint)s
)
ON CONFLICT (fingerprint) DO NOTHING
"""

batch = []
line_no = 0
errors = 0
inserted = 0

with open(FILE_PATH, "r", encoding="utf-8") as fh:
    for line in fh:
        line_no += 1
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception as e:
            print(f"JSON parse error line {line_no}: {e}", file=sys.stderr)
            errors += 1
            continue

        # собираем словарь для вставки
        rec = {
            "flight_id": normalize_value(data.get("flight_id")),
            "uav_type": normalize_value(data.get("uav_type")),
            "start_time": normalize_value(data.get("start_time")),   # ISO string ok
            "end_time": normalize_value(data.get("end_time")),
            "duration_seconds": normalize_value(data.get("duration_seconds")),
            "start_lat": normalize_value(data.get("start_lat")),
            "start_lon": normalize_value(data.get("start_lon")),
            "end_lat": normalize_value(data.get("end_lat")),
            "end_lon": normalize_value(data.get("end_lon")),
            "time_token": normalize_value(data.get("time_token")),
            "raw_payload": json.dumps(data.get("raw_payload")) if data.get("raw_payload") is not None else None,
            "fingerprint": normalize_value(data.get("fingerprint")),
        }

        batch.append(rec)

        if len(batch) >= BATCH_SIZE:
            try:
                execute_batch(cur, insert_sql, batch, page_size=BATCH_SIZE)
                conn.commit()
                inserted += len(batch)
            except Exception as e:
                conn.rollback()
                print(f"DB error on batch ending at line {line_no}: {e}", file=sys.stderr)
                errors += len(batch)
            batch = []

# вставляем остаток
if batch:
    try:
        execute_batch(cur, insert_sql, batch, page_size=len(batch))
        conn.commit()
        inserted += len(batch)
    except Exception as e:
        conn.rollback()
        print(f"DB error on final batch: {e}", file=sys.stderr)
        errors += len(batch)

cur.close()
conn.close()

print(f"Done. Lines processed: {line_no}, inserted attempts: {inserted}, errors: {errors}")
