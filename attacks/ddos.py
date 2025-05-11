import requests
import random
import time

url = "http://localhost:30500/"

for _ in range(2000):
    ip = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
    headers = {
        "X-Forwarded-For": ip,
        "User-Agent": f"BotSim/{random.randint(1,5)}.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=1)
        print(f"Sent from {ip}: {response.status_code}")
    except Exception as e:
        print(f"Error from {ip}: {e}")
    time.sleep(0.01)  # Optional: Add delay to simulate realistic load
