# upload_via_requests.py
import requests
token = "supersecret123"
url = "http://localhost:8000/api/v1/upload"
files = {"file": open("data/parsed_normalized.ndjson","rb")}
r = requests.post(url, files=files, headers={"Authorization": f"Bearer {token}"})
print(r.status_code, r.text)
