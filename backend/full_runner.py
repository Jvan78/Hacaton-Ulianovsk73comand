# full_runner.py
import json
import math
import pandas as pd
from app.parser import normalize_row

EXCEL_PATH = "../data/2025.xlsx"   # или путь к большему файлу
OUT_PATH = "parsed.ndjson"         # newline-delimited JSON, удобно для импорта
CHUNK = 1000                       # размер чанка (настраивай)

def safe_convert(obj):
    # replace NaN/inf -> None in nested dicts
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        return None
    if isinstance(obj, dict):
        return {k: safe_convert(v) for k,v in obj.items()}
    if isinstance(obj, list):
        return [safe_convert(x) for x in obj]
    return obj

def process():
    df = pd.read_excel(EXCEL_PATH)
    total = 0
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for start in range(0, len(df), CHUNK):
            sub = df.iloc[start:start + CHUNK]
            for _, row in sub.iterrows():
                row_dict = row.to_dict()
                parsed = normalize_row(row_dict)
                cleaned = safe_convert(parsed)
                out.write(json.dumps(cleaned, ensure_ascii=False) + "\n")
                total += 1
            print("Processed", total)
    print("Done. total:", total)

if __name__ == "__main__":
    process()
