import pytest

from iotgis.geo import haversine_km, nearest, to_geojson
from iotgis.rules import classify, validate
from iotgis.server import create_app


def test_classify_levels():
    assert classify(40, 1, 90) == "NORMAL"
    assert classify(70, 1, 90) == "WARNING"
    assert classify(40, 1, 10) == "WARNING"
    assert classify(85, 1, 90) == "CRITICAL"
    assert classify(40, 7.5, 90) == "CRITICAL"


def test_validate():
    assert validate({"asset_id": "X", "temperature": 1, "vibration": 1, "battery": 50}) == []
    assert validate({"asset_id": "X"})
    assert validate({"asset_id": "X", "temperature": "a", "vibration": 1, "battery": 50})
    assert validate({"asset_id": "X", "temperature": 1, "vibration": 1, "battery": 150})


def test_haversine_known_distance():
    # Jakarta ke Bandung sekitar 116 km
    assert haversine_km(-6.2088, 106.8456, -6.9175, 107.6191) == pytest.approx(116, abs=3)
    assert haversine_km(1, 1, 1, 1) == 0


def test_nearest_and_geojson():
    cands = [{"id": "a", "lat": 0, "lon": 0}, {"id": "b", "lat": 1, "lon": 1}]
    c, d = nearest(0.9, 0.9, cands)
    assert c["id"] == "b" and d < 20
    gj = to_geojson([{"lat": -3.8, "lon": 102.2, "name": "x"}])
    assert gj["features"][0]["geometry"]["coordinates"] == [102.2, -3.8]


def test_api_flow(tmp_path):
    client = create_app(str(tmp_path / "t.db")).test_client()
    ok = client.post("/api/telemetry", json={"asset_id": "PMP-01", "temperature": 90,
                                              "vibration": 1, "battery": 80})
    assert ok.status_code == 201 and ok.get_json()["status"] == "CRITICAL"
    assert client.post("/api/telemetry", json={"asset_id": "NOPE", "temperature": 1,
                                                "vibration": 1, "battery": 80}).status_code == 404
    assert client.post("/api/telemetry", json={"asset_id": "PMP-01"}).status_code == 400
    latest = client.get("/api/latest").get_json()
    assert len(latest) == 1 and latest[0]["status"] == "CRITICAL"
    assert client.get("/api/geojson").get_json()["type"] == "FeatureCollection"
