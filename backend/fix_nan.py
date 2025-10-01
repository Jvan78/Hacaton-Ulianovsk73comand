# fix_nan.py
import json
import math

IN_FILE = "sample_parsed.json"
OUT_FILE = "sample_parsed_clean.json"

def fix_nan(obj):
    """Рекурсивно заменяем NaN на None"""
    if isinstance(obj, dict):
        return {k: fix_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_nan(i) for i in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj

def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    clean_data = fix_nan(data)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)

    print(f"Cleaned JSON saved to {OUT_FILE}")

if __name__ == "__main__":
    main()
