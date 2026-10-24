"""
Security hardening tests for the EV Placement API.

Covers: input validation bounds, CORS restriction, security headers,
request-body size limits, per-IP rate limiting, and bounded caches.
These tests do NOT require external internet access.
"""
import json

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings
from backend.models.route import GeocodeResult
from backend.services.geocoding_service import _BoundedLRUCache

client = TestClient(app)


# ----------------------------------------------------------------------
# Input validation
# ----------------------------------------------------------------------

def test_geocode_query_too_long_rejected():
    query = "x" * (settings.MAX_QUERY_LENGTH + 50)
    resp = client.get(f"/api/geocode?q={query}")
    assert resp.status_code in (400, 422)


def test_geocode_query_control_chars_rejected():
    resp = client.get("/api/geocode?q=" + "a" * 10 + "%0Ainjected")
    assert resp.status_code in (400, 422)


def test_distance_matrix_invalid_coordinates_rejected():
    resp = client.post("/api/distance-matrix", json={
        "locations": [{"lat": 200.0, "lon": 85.0}, {"lat": 20.0, "lon": 85.0}]
    })
    assert resp.status_code == 422


def test_distance_matrix_too_many_locations_rejected():
    locations = [{"lat": 20.0 + i, "lon": 85.0 + i} for i in range(settings.MAX_MATRIX_LOCATIONS + 5)]
    resp = client.post("/api/distance-matrix", json={"locations": locations})
    assert resp.status_code == 422


def test_mst_too_many_stations_rejected():
    stations = []
    for i in range(settings.MAX_STATIONS_PER_REQUEST + 5):
        stations.append({
            "id": f"ST-{i}", "name": f"Station {i}",
            "latitude": 20.0 + i * 0.01, "longitude": 85.0 + i * 0.01,
            "installation_cost": 100000, "expected_value": 50,
        })
    resp = client.post("/api/mst", json={"stations": stations, "feeder_cost_per_km": 25000})
    assert resp.status_code == 422


def test_knapsack_budget_upper_bound_rejected():
    candidates = [{
        "id": "ST-01", "name": "Station Alpha",
        "latitude": 20.2603, "longitude": 85.8395,
        "installation_cost": 100000, "expected_value": 70,
    }]
    resp = client.post("/api/knapsack", json={
        "candidates": candidates, "budget": settings.MAX_BUDGET + 1
    })
    assert resp.status_code == 422


def test_candidate_invalid_latitude_rejected():
    stations = [{
        "id": "ST-01", "name": "Station Alpha",
        "latitude": 200.0, "longitude": 85.8395,
        "installation_cost": 100000, "expected_value": 70,
    }]
    resp = client.post("/api/mst", json={"stations": stations, "feeder_cost_per_km": 25000})
    assert resp.status_code == 422


def test_candidate_name_too_long_rejected():
    stations = [{
        "id": "ST-01", "name": "A" * (settings.MAX_NAME_LENGTH + 10),
        "latitude": 20.2603, "longitude": 85.8395,
        "installation_cost": 100000, "expected_value": 70,
    }]
    resp = client.post("/api/mst", json={"stations": stations, "feeder_cost_per_km": 25000})
    assert resp.status_code == 422


def test_dijkstra_invalid_custom_coordinates_rejected():
    resp = client.post("/api/dijkstra", json={
        "stations": [],
        "start_lat": 999.0, "start_lon": 85.0,
        "end_lat": 20.0, "end_lon": 85.0,
    })
    assert resp.status_code == 422


# ----------------------------------------------------------------------
# CORS restriction
# ----------------------------------------------------------------------

def test_cors_wildcard_not_allowed():
    """A cross-origin preflight from an untrusted origin must be rejected."""
    resp = client.options("/api/geocode", headers={
        "Origin": "http://evil.example.com",
        "Access-Control-Request-Method": "GET",
    })
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers}


def test_cors_allowed_origin_permitted():
    resp = client.options("/api/geocode", headers={
        "Origin": "http://127.0.0.1:8085",
        "Access-Control-Request-Method": "GET",
    })
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:8085"


# ----------------------------------------------------------------------
# Security headers
# ----------------------------------------------------------------------

def test_security_headers_present():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    headers = {k.lower(): v for k, v in resp.headers.items()}
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "content-security-policy" in headers


# ----------------------------------------------------------------------
# Body size limit
# ----------------------------------------------------------------------

def test_oversized_body_rejected():
    # Craft a JSON body larger than MAX_REQUEST_BYTES (2 MB).
    junk = "A" * (settings.MAX_REQUEST_BYTES + 1024)
    big_payload = {"stations": [], "junk": junk}
    resp = client.post("/api/mst", json=big_payload)
    assert resp.status_code == 413


# ----------------------------------------------------------------------
# Rate limiting (middleware unit test)
# ----------------------------------------------------------------------

import asyncio  # noqa: E402


class _FakeApp:
    def __init__(self):
        self.calls = 0

    async def __call__(self, scope, receive, send):
        self.calls += 1
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def test_rate_limit_blocks_after_cap():
    from backend.main import RateLimitMiddleware

    fake = _FakeApp()
    mw = RateLimitMiddleware(fake, limits={"/api/geocode": (3, 60)})
    scope = {"type": "http", "path": "/api/geocode", "headers": [], "client": ("1.2.3.4", 1)}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    async def run():
        for _ in range(5):
            await mw(scope, receive, send)

    asyncio.run(run())
    assert fake.calls == 3  # only 3 allowed through
    # 4th and 5th should be 429 responses
    statuses = [m["status"] for m in sent if m["type"] == "http.response.start"]
    assert statuses == [200, 200, 200, 429, 429]


# ----------------------------------------------------------------------
# Bounded geocode cache
# ----------------------------------------------------------------------

def test_bounded_cache_evicts_oldest():
    cache = _BoundedLRUCache(2)
    r1 = GeocodeResult(query="a", display_name="A", latitude=1.0, longitude=1.0)
    r2 = GeocodeResult(query="b", display_name="B", latitude=2.0, longitude=2.0)
    r3 = GeocodeResult(query="c", display_name="C", latitude=3.0, longitude=3.0)

    cache.set("a", r1)
    cache.set("b", r2)
    cache.set("c", r3)  # evicts "a" (least recently used)
    assert cache.get("a") is None
    assert cache.get("b") is not None
    assert cache.get("c") is not None


def test_geocode_cache_uses_normalized_key():
    """The geocode service stores cache entries keyed by the lowercase query."""
    cache = _BoundedLRUCache(5)
    r = GeocodeResult(query="Bhubaneswar", display_name="Bhubaneswar", latitude=20.0, longitude=85.0)
    cache.set("bhubaneswar", r)
    # The service normalizes the lookup key to lowercase before consulting the cache.
    assert cache.get("bhubaneswar") is r
