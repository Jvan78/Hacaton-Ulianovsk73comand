# get_token_and_call.py
import requests

BASE = "http://localhost:8000"
username = "admin"
password = "password123"

# 1) получить токен
r = requests.post(f"{BASE}/token", data={"username": username, "password": password})
print("token endpoint status:", r.status_code)
print("token response:", r.text)
if r.status_code != 200:
    raise SystemExit("Token request failed")

token = r.json().get("access_token")
if not token:
    raise SystemExit("No access_token in response")

# 2) вызвать защищённый эндпоинт
h = {"Authorization": f"Bearer {token}"}
r2 = requests.get(f"{BASE}/api/v1/top-regions", headers=h)
print("top-regions status:", r2.status_code)
print(r2.text)
