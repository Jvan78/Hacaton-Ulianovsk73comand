import requests
token = "supersecret123"
url = "http://localhost:8000/api/v1/upload"
with open("data/parsed_normalized.ndjson", "rb") as fh:
    files = {"file": ("parsed_normalized.ndjson", fh, "application/octet-stream")}
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, files=files)
print(r.status_code, r.text)
