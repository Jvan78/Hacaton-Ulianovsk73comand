# clean_json.py
import json
import math

IN_PATH = "sample_parsed.json"
OUT_PATH = "sample_parsed_clean.json"

def clean_value(value):
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value

def clean_row(row):
    return {k: clean_value(v) for k, v in row.items()}

def main():
    with open(IN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = [clean_row(row) for row in data]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print(f"Cleaned {len(cleaned_data)} records. Saved to {OUT_PATH}")

if __name__ == "__main__":
    main()
