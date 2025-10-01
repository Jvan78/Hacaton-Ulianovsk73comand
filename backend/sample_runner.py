# backend/sample_runner.py
import json
import pandas as pd
from app.parser import normalize_row

EXCEL_PATH = "../data/2025.xlsx"   # путь к файлу Excel (от папки backend)
N = 500                            # сколько строк взять

def row_to_dict(row, df_columns):
    # Собираем словарь и явно складываем текстовые блоки в raw_payload поля
    d = {}
    for c in df_columns:
        d[c] = row[c] if c in row else None
    # не кладём NaN в raw_payload, normalize_row сам соберёт нужное
    return d

def main():
    df = pd.read_excel(EXCEL_PATH, dtype=object)  # читаем как объекты, чтобы не терять текст
    n = min(N, len(df))
    results = []
    for i in range(n):
        row = df.iloc[i]
        row_dict = row_to_dict(row, df.columns)
        row_dict["__row_index"] = int(i)
        parsed = normalize_row(row_dict)
        results.append(parsed)

    out_path = "sample_parsed.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} parsed records to {out_path}")

if __name__ == "__main__":
    main()
