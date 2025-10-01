# call_protected_endpoints.py
import requests, os, sys

BASE = "http://localhost:8000"
TOKEN = os.environ.get("TOKEN") or "<PASTE_YOUR_TOKEN_HERE>"

h = {"Authorization": f"Bearer {TOKEN}"}

# 1) top regions
r = requests.get(f"{BASE}/api/v1/top-regions", headers=h, params={"limit": 10})
print("top-regions:", r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)

# 2) list flights (first page)
r2 = requests.get(f"{BASE}/api/v1/flights", headers=h, params={"limit": 10, "offset": 0})
print("flights:", r2.status_code)
try:
    for f in r2.json():
        print(f)
except Exception:
    print(r2.text)
