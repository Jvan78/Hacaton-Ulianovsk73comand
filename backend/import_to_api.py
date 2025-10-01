# import_to_api.py
import json, time, math, requests

API_URL = "http://localhost:8000/api/v1/import"
BATCH_SIZE = 200

def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k,v in obj.items() if v is not None and not (isinstance(v,float) and math.isnan(v))}
    if isinstance(obj, list):
        return [clean_for_json(x) for x in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj

def send_batch(batch):
    cleaned = [clean_for_json(x) for x in batch]
    resp = requests.post(API_URL, json=cleaned, timeout=60)
    resp.raise_for_status()
    return resp.json()

def main():
    items = json.load(open("sample_parsed_clean.json", encoding="utf-8"))
    # map if needed to FlightIn shape — assuming shape matches
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i+BATCH_SIZE]
        print("Sending", i, "->", i+len(batch)-1)
        try:
            r = send_batch(batch)
            print("Response:", r)
        except Exception as e:
            print("Error", e)
        time.sleep(0.5)

if __name__ == "__main__":
    main()