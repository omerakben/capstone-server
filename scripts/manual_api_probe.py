"""Manual probe script for local API testing.

Run with: python scripts/manual_api_probe.py
"""
import json

import requests

url = "http://localhost:8000/api/v1/workspaces/3/artifacts/3/"
headers = {"Content-Type": "application/json"}
data = {"tags": [1, 4]}

def main():
    try:
        resp = requests.patch(url, headers=headers, json=data)
        print("Status Code:", resp.status_code)
        try:
            print("Response JSON:", json.dumps(resp.json(), indent=2))
        except Exception:
            print("Response Text:", resp.text)
    except Exception as e:
        print("Request Error:", e)

if __name__ == "__main__":
    main()
