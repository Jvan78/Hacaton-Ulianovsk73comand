# prepare_api_payload.py
import json
import argparse
import math
from datetime import date

def safe_float(v):
    if v is None:
        return None
    try:
        # sometimes pandas writes numpy floats -> check NaN
        if isinstance(v, float) and math.isnan(v):
            return None
        return float(v)
    except Exception:
        return None

def format_time_from_token(token, default_date):
    # token like "0715" -> "YYYY-MM-DDT07:15:00Z"
    if not token:
        return None
    s = str(token).strip()
    if len(s) >= 3 and s.isdigit():
        # ensure HHMM
        if len(s) == 3:
            s = "0" + s
        hh = s[:2]
        mm = s[2:4]
        return f"{default_date}T{hh}:{mm}:00Z"
    return None

def map_record(r, default_date):
    # r is record from sample_parsed.json
    start_time = r.get("start_time") or format_time_from_token(r.get("time_token"), default_date)
    if start_time is None:
        # fallback to default_date midnight, to satisfy validator
        start_time = f"{default_date}T00:00:00Z"
    return {
        "flight_id": r.get("flight_id"),
        "uav_type": r.get("uav_type"),
        "start_time": start_time,
        "end_time": r.get("end_time"),
        "duration_seconds": r.get("duration_seconds"),
        "start_lat": safe_float(r.get("start_lat")),
        "start_lon": safe_float(r.get("start_lon")),
        "end_lat": safe_float(r.get("end_lat")),
        "end_lon": safe_float(r.get("end_lon")),
        "raw": r.get("raw_payload") or r.get("raw") or {}
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="sample_parsed.json")
    p.add_argument("--output", default="api_payload.json")
    p.add_argument("--date", default=str(date.today()))
    args = p.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    mapped = []
    skipped = 0
    for i, rec in enumerate(data):
        try:
            m = map_record(rec, args.date)
            mapped.append(m)
        except Exception as e:
            skipped += 1
            print("Skip record", i, e)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(mapped, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(mapped)} records to {args.output}. Skipped: {skipped}")

if __name__ == "__main__":
    main()
