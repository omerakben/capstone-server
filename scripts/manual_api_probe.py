"""Manual probe script for local API testing.

Usage:
  API_BASE_URL=http://localhost:8000/api/v1 \
  WORKSPACE_ID=1 ARTIFACT_ID=1 TOKEN=eyJ... \
  python scripts/manual_api_probe.py
"""
import json
import os

import requests

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")
WS_ID = os.environ.get("WORKSPACE_ID", "1")
ART_ID = os.environ.get("ARTIFACT_ID", "1")
TOKEN = os.environ.get("TOKEN")  # Optional Firebase ID token

URL = f"{API_BASE}/workspaces/{WS_ID}/artifacts/{ART_ID}/"
HEADERS = {"Content-Type": "application/json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

DATA = {"tags": [1]}

def main():
    try:
        resp = requests.patch(URL, headers=HEADERS, json=DATA, timeout=10)
        print("Status Code:", resp.status_code)
        try:
            print("Response JSON:", json.dumps(resp.json(), indent=2))
        except Exception:
            print("Response Text:", resp.text[:500])
    except Exception as e:
        print("Request Error:", e)

if __name__ == "__main__":
    main()
