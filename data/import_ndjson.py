import json
import psycopg2
from psycopg2 import extras  # <- обязательно импортируем extras

# Путь к файлу
FILE_PATH = r"C:\Users\Admin\PycharmProjects\PythonProject8\Hacatonreal\data\parsed.ndjson"

# Параметры подключения
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "gis"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Подключение
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

# Создание таблицы, если не существует
cur.execute("""
CREATE TABLE IF NOT EXISTS staging_raw (
    raw jsonb
);
TRUNCATE staging_raw;
""")
conn.commit()

# Вставка пачками
batch = []
batch_size = 1000
with open(FILE_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            batch.append((line,))
        if len(batch) >= batch_size:
            extras.execute_values(
                cur,
                "INSERT INTO staging_raw(raw) VALUES %s ON CONFLICT DO NOTHING",
                batch
            )
            conn.commit()
            batch = []

# Остаток
if batch:
    extras.execute_values(
        cur,
        "INSERT INTO staging_raw(raw) VALUES %s ON CONFLICT DO NOTHING",
        batch
    )
    conn.commit()

cur.close()
conn.close()

print("Импорт завершен!")
