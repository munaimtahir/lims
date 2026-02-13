
import requests
import time
import sys
import json

PROXY_URL = "http://127.0.0.1:8012"
HEALTH_URL = f"{PROXY_URL}/api/v1/health/"
LOGIN_URL = f"{PROXY_URL}/api/v1/auth/login/"

def wait_for_health():
    print("Waiting for health check...")
    for i in range(30):
        try:
            response = requests.get(HEALTH_URL, timeout=5)
       cd     if response.status_code == 200:
                print("Health check passed!")
                print(response.json())
                return True
            else:
                print(f"Health check failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Connection failed: {e}")
        time.sleep(2)
    return False

def check_login():
    print("Attempting login...")
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    headers = {
        "Content-Type": "application/json",
        "Host": "lims.alshifalab.pk" # Mimic external host
    }
    try:
        response = requests.post(LOGIN_URL, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            print("Login successful!")
            print(f"Token received: {response.json().get('access') is not None}")
            return True
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Login exception: {e}")
        return False

def main():
    if not wait_for_health():
        sys.exit(1)
    
    if not check_login():
        sys.exit(1)
    
    print("Deployment verification successful!")

if __name__ == "__main__":
    main()
