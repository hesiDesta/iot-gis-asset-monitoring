"""Simulator node IoT: mengirim data sensor palsu ke server.
Berguna untuk uji coba tanpa perangkat keras ESP32."""
import argparse
import random
import time

import requests

from .server import load_assets

# Aset yang sengaja dibuat bermasalah agar analisis punya hasil menarik
FAULTY = {"PMP-02": "CRITICAL", "TRF-03": "CRITICAL", "GEN-02": "WARNING", "LMP-02": "WARNING"}


def make_reading(asset_id, rng):
    mode = FAULTY.get(asset_id, "NORMAL")
    if mode == "CRITICAL":
        temp, vib = rng.uniform(82, 95), rng.uniform(5, 9)
    elif mode == "WARNING":
        temp, vib = rng.uniform(66, 78), rng.uniform(2, 5)
    else:
        temp, vib = rng.uniform(35, 58), rng.uniform(0.5, 3)
    battery = rng.uniform(8, 18) if asset_id == "LMP-02" else rng.uniform(40, 100)
    return {"asset_id": asset_id, "temperature": round(temp, 1),
            "vibration": round(vib, 2), "battery": round(battery, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:5000/api/telemetry")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--interval", type=float, default=0.5, help="jeda antar ronde (detik)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    ids = list(load_assets())
    for r in range(args.rounds):
        for aid in ids:
            resp = requests.post(args.url, json=make_reading(aid, rng), timeout=5)
            print(f"ronde {r + 1} {aid}: {resp.status_code} {resp.json()}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
