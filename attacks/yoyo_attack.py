#!/usr/bin/env python3
import threading, requests, random, time
from datetime import datetime

URL            = "http://localhost:30500/"
THREADS        = 10
ATTACK_SEC     = 2 * 60
COOLDOWN_SEC   = 1 * 60
REQUEST_DELAY  = 0.1

attack_event = threading.Event()

def worker(thread_id):
    while True:
        if attack_event.is_set():
            ip = f"192.168.1.{random.randint(1,10)}"
            ua = f"AttackBot/{random.randint(1,5)}.0"
            try:
                r = requests.get(URL, headers={
                    "X-Forwarded-For": ip,
                    "User-Agent": ua
                }, timeout=1)
                print(f"[{thread_id}] {datetime.now():%H:%M:%S} → {r.status_code} from {ip}")
            except Exception as e:
                print(f"[{thread_id}] {datetime.now():%H:%M:%S} err {e}")
            time.sleep(REQUEST_DELAY)
        else:
            time.sleep(1)  # cooldown idle

def cycle():
    while True:
        print(f"\n=== ATTACK for {ATTACK_SEC//60}m === {datetime.now()}\n")
        attack_event.set()
        time.sleep(ATTACK_SEC)

        print(f"\n=== COOLDOWN for {COOLDOWN_SEC//60}m === {datetime.now()}\n")
        attack_event.clear()
        time.sleep(COOLDOWN_SEC)

if __name__ == "__main__":
    for i in range(THREADS):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
    cycle()
