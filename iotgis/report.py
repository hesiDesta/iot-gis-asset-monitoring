"""Analisis spasial + pembuatan peta dan work order perawatan."""
import argparse
import csv
import json
import os
import sqlite3

import folium

from .geo import nearest, to_geojson
from .server import BASE, latest_per_asset, load_assets

COLORS = {"NORMAL": "green", "WARNING": "orange", "CRITICAL": "red"}
PRIORITY = {"CRITICAL": 1, "WARNING": 2}


def load_teams():
    with open(os.path.join(BASE, "data", "teams.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["lat"], r["lon"] = float(r["lat"]), float(r["lon"])
    return rows


def build_work_orders(latest, teams):
    """Untuk aset bermasalah: pilih tim terdekat, urutkan menurut prioritas lalu jarak."""
    orders = []
    for a in latest:
        if a["status"] == "NORMAL":
            continue
        team, dist = nearest(a["lat"], a["lon"], teams)
        orders.append({"priority": PRIORITY[a["status"]], "asset_id": a["asset_id"],
                       "asset": a["name"], "status": a["status"],
                       "team": team["name"], "distance_km": round(dist, 2)})
    return sorted(orders, key=lambda o: (o["priority"], o["distance_km"]))


def build_map(latest, teams, path):
    center = [sum(a["lat"] for a in latest) / len(latest),
              sum(a["lon"] for a in latest) / len(latest)]
    m = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")
    for a in latest:
        popup = (f"<b>{a['name']}</b> ({a['asset_id']})<br>Status: {a['status']}<br>"
                 f"Suhu: {a['temperature']} C<br>Getaran: {a['vibration']} mm/s<br>"
                 f"Baterai: {a['battery']}%")
        folium.CircleMarker([a["lat"], a["lon"]], radius=9, color=COLORS[a["status"]],
                            fill=True, fill_opacity=0.8,
                            popup=folium.Popup(popup, max_width=260)).add_to(m)
    for t in teams:
        folium.Marker([t["lat"], t["lon"]], tooltip=t["name"],
                      icon=folium.Icon(color="blue", icon="wrench", prefix="fa")).add_to(m)
    m.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(BASE, "iot_gis.db"))
    ap.add_argument("--out", default=os.path.join(BASE, "outputs"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    latest = latest_per_asset(conn, load_assets())
    conn.close()
    if not latest:
        raise SystemExit("Belum ada data telemetry. Jalankan simulator dulu.")
    teams = load_teams()

    build_map(latest, teams, os.path.join(args.out, "map.html"))
    with open(os.path.join(args.out, "assets_status.geojson"), "w", encoding="utf-8") as f:
        json.dump(to_geojson(latest), f, indent=2)

    orders = build_work_orders(latest, teams)
    with open(os.path.join(args.out, "work_orders.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["priority", "asset_id", "asset", "status", "team", "distance_km"])
        w.writeheader()
        w.writerows(orders)

    counts = {s: sum(1 for a in latest if a["status"] == s) for s in COLORS}
    print("Ringkasan status:", counts)
    print("Work order (prioritas -> jarak):")
    for o in orders:
        print(f"  P{o['priority']} {o['asset_id']} {o['status']:<8} -> {o['team']} ({o['distance_km']} km)")
    print(f"Output di: {args.out}")


if __name__ == "__main__":
    main()
