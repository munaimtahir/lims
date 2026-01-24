
import requests
import json
session = requests.Session()
session.headers.update({"X-Forwarded-Proto": "https"})

try:
    auth = session.post("http://localhost:8000/api/v1/auth/login/", json={"username": "receptionist", "password": "recep123"})
    token = auth.json()['data']['access_token']
    
    resp = session.get("http://localhost:8000/api/v1/laboratory/tests/", headers={"Authorization": f"Bearer {token}"})
    print(resp.status_code)
    data = resp.json()
    if 'results' in data:
        results = data['results']
        if len(results) > 0:
            print("First item keys:", results[0].keys())
            print("First item:", results[0])
        else:
            print("No results found")
    else:
        print("No results key", data.keys())

except Exception as e:
    print(e)
