"""Fungsi analisis spasial dasar (tanpa dependensi GIS berat)."""
import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Jarak lingkaran besar antara dua titik koordinat, dalam km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest(lat, lon, candidates):
    """Cari kandidat terdekat. candidates: list dict dengan 'lat' dan 'lon'.
    Mengembalikan (kandidat, jarak_km)."""
    best, best_d = None, float("inf")
    for c in candidates:
        d = haversine_km(lat, lon, c["lat"], c["lon"])
        if d < best_d:
            best, best_d = c, d
    return best, best_d


def to_geojson(features_rows):
    """Ubah list dict (punya lat, lon) menjadi GeoJSON FeatureCollection.
    Urutan koordinat GeoJSON adalah [lon, lat]. Cocok dibuka di QGIS."""
    features = []
    for row in features_rows:
        props = {k: v for k, v in row.items() if k not in ("lat", "lon")}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}
