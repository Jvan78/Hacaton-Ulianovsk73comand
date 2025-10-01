# sanitize_json.py
import json, math, sys
from pathlib import Path

p = Path("sample_parsed.json")
if not p.exists():
    print("sample_parsed.json not found")
    sys.exit(1)

def clean_obj(o):
    if isinstance(o, dict):
        return {k: clean_obj(v) for k,v in o.items() if v is not None and not (isinstance(v,float) and math.isnan(v))}
    if isinstance(o, list):
        return [clean_obj(i) for i in o]
    if isinstance(o, float):
        if math.isnan(o): return None
    return o

data = json.load(open(p, encoding="utf-8"))
cleaned = clean_obj(data)
with open("sample_parsed_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)
print("Wrote sample_parsed_clean.json")
