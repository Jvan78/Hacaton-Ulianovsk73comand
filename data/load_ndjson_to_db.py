# load_ndjson_to_db.py
import json
import os
import sys
from psycopg2 import connect, sql, extras

# Настройки подключения - при необходимости поправь
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "gis")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

NDJSON_PATH = "parsed.ndjson"   # путь к файлу (от папки backend)
BATCH = 1000

def pg_connect():
    return connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=10
    )

def ensure_table():
    q = """
    CREATE TABLE IF NOT EXISTS staging_raw (raw jsonb);
    TRUNCATE staging_raw;
    """
    with pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            conn.commit()
    print("staging_raw ready (created/truncated).")

def load_file(path):
    total = 0
    bad = 0
    batch = []
    with open(path, "r", encoding="utf-8") as f, open("bad_lines.log", "w", encoding="utf-8") as badf:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                # валидируем JSON теперь (throws if invalid)
                obj = json.loads(s)
                # store Python obj (we'll use json.dumps when sending to DB)
                batch.append(json.dumps(obj, ensure_ascii=False))
            except Exception as e:
                bad += 1
                badf.write(f"{line_no}\t{e}\t{line}\n")
                # не прерываем загрузку
            if len(batch) >= BATCH:
                flush_batch(batch)
                total += len(batch)
                print(f"Inserted {total} rows...")
                batch = []
        if batch:
            flush_batch(batch)
            total += len(batch)
    print(f"Done. inserted ~{total} rows; bad lines: {bad}. See bad_lines.log for details.")

def flush_batch(batch):
    # batch: list of JSON strings (unicode)
    # use psycopg2.extras.execute_values for fast multi-insert
    with pg_connect() as conn:
        with conn.cursor() as cur:
            # create tuple list for execute_values: (jsonb,)
            vals = [(extras.Json(json.loads(s)),) for s in batch]
            extras.execute_values(cur,
                "INSERT INTO staging_raw (raw) VALUES %s",
                vals,
                template=None,
                page_size=500
            )
            conn.commit()

if __name__ == "__main__":
    if not os.path.exists(NDJSON_PATH):
        print(f"File {NDJSON_PATH} not found. Run from folder with parsed.ndjson")
        sys.exit(1)
    ensure_table()
    load_file(NDJSON_PATH)
