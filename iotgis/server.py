"""Server penerima data IoT (Flask + SQLite)."""
import csv
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

from .geo import to_geojson
from .rules import classify, validate

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_CSV = os.path.join(BASE, "data", "assets.csv")

SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    temperature REAL NOT NULL,
    vibration REAL NOT NULL,
    battery REAL NOT NULL,
    status TEXT NOT NULL,
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tel_asset_ts ON telemetry(asset_id, ts);
"""


def load_assets(path=ASSETS_CSV):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["lat"], r["lon"] = float(r["lat"]), float(r["lon"])
    return {r["asset_id"]: r for r in rows}


def latest_per_asset(conn, assets):
    """Pembacaan terbaru tiap aset, digabung dengan metadata lokasinya."""
    rows = conn.execute(
        """SELECT t.* FROM telemetry t
           JOIN (SELECT asset_id, MAX(id) mid FROM telemetry GROUP BY asset_id) m
             ON t.id = m.mid"""
    ).fetchall()
    out = []
    for r in rows:
        a = assets.get(r["asset_id"])
        if not a:
            continue
        out.append({**a, "temperature": r["temperature"], "vibration": r["vibration"],
                    "battery": r["battery"], "status": r["status"], "ts": r["ts"]})
    return out


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", os.path.join(BASE, "iot_gis.db"))
    app.config["ASSETS"] = load_assets()

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        conn.executescript(SCHEMA)

    @app.post("/api/telemetry")
    def ingest():
        payload = request.get_json(silent=True) or {}
        problems = validate(payload)
        if problems:
            return jsonify(error=problems), 400
        if payload["asset_id"] not in app.config["ASSETS"]:
            return jsonify(error=["asset_id tidak terdaftar"]), 404
        status = classify(payload["temperature"], payload["vibration"], payload["battery"])
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn = db()
        conn.execute(
            "INSERT INTO telemetry(asset_id,temperature,vibration,battery,status,ts) VALUES (?,?,?,?,?,?)",
            (payload["asset_id"], payload["temperature"], payload["vibration"],
             payload["battery"], status, ts),
        )
        conn.commit()
        return jsonify(asset_id=payload["asset_id"], status=status), 201

    @app.get("/api/latest")
    def latest():
        return jsonify(latest_per_asset(db(), app.config["ASSETS"]))

    @app.get("/api/geojson")
    def geojson():
        return jsonify(to_geojson(latest_per_asset(db(), app.config["ASSETS"])))

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
