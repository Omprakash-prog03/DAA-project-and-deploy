import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Kruskal's Minimum Spanning Tree (Hand-written)" in data["algorithms"]

@pytest.mark.external_api
def test_real_geocoding_bhubaneswar():
    resp = client.get("/api/geocode?q=Bhubaneswar")
    assert resp.status_code == 200
    data = resp.json()
    assert "Bhubaneswar" in data["display_name"]
    assert 20.0 <= data["latitude"] <= 21.0
    assert 85.0 <= data["longitude"] <= 86.5
    assert data["data_source"] == "OpenStreetMap Nominatim"

@pytest.mark.external_api
def test_geocoding_invalid_query():
    resp = client.get("/api/geocode?q=xyzqwe12345nonexistentcity")
    assert resp.status_code == 404
    assert "No geographic location found" in resp.json()["detail"]

def test_charging_stations_endpoint():
    # Bhubaneswar coordinates
    resp = client.get("/api/charging-stations?lat=20.2603&lon=85.8395&radius=35&max_results=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Even if 0 stations in rural areas, it must return valid list structure, never fake stations
    for st in data:
        assert "name" in st
        assert "latitude" in st
        assert "longitude" in st
        assert st["data_source"] in ("Open Charge Map API", "OpenStreetMap (Overpass Infrastructure API)")

def test_distance_matrix_endpoint():
    locs = [
        {"lat": 20.2603, "lon": 85.8395},
        {"lat": 20.2961, "lon": 85.8245},
        {"lat": 20.3533, "lon": 85.8198}
    ]
    resp = client.post("/api/distance-matrix", json={"locations": locs})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["distances_km"]) == 3
    assert len(data["distances_km"][0]) == 3
    # Diagonal distance must be 0
    assert data["distances_km"][0][0] == 0.0
    # Positive distances between distinct locations
    assert data["distances_km"][0][1] > 0.0

def test_kruskal_mst_endpoint():
    stations = [
        {
            "id": "ST-01", "name": "Station Alpha",
            "latitude": 20.2603, "longitude": 85.8395,
            "installation_cost": 100000, "expected_value": 70, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        },
        {
            "id": "ST-02", "name": "Station Beta",
            "latitude": 20.2961, "longitude": 85.8245,
            "installation_cost": 120000, "expected_value": 85, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        },
        {
            "id": "ST-03", "name": "Station Gamma",
            "latitude": 20.3533, "longitude": 85.8198,
            "installation_cost": 90000, "expected_value": 60, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        }
    ]
    resp = client.post("/api/mst", json={"stations": stations, "feeder_cost_per_km": 25000})
    assert resp.status_code == 200
    data = resp.json()
    # 3 nodes in connected tree -> 2 accepted edges
    assert len(data["accepted_edges"]) == 2
    assert data["total_backbone_km"] > 0.0
    assert data["backbone_cost"] == int(round(data["total_backbone_km"] * 25000))
    assert "Kruskal" in data["algorithm_info"]["algorithm"]

def test_dijkstra_endpoint():
    stations = [
        {
            "id": "ST-01", "name": "Station Alpha",
            "latitude": 20.2603, "longitude": 85.8395,
            "installation_cost": 100000, "expected_value": 70, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        },
        {
            "id": "ST-02", "name": "Station Beta",
            "latitude": 20.2961, "longitude": 85.8245,
            "installation_cost": 120000, "expected_value": 85, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        }
    ]
    resp = client.post("/api/dijkstra", json={
        "stations": stations,
        "start_id": "ST-01",
        "destination_id": "ST-02"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["start_id"] == "ST-01"
    assert data["destination_id"] == "ST-02"
    assert data["total_distance_km"] > 0.0
    assert data["path_node_ids"] == ["ST-01", "ST-02"]

def test_knapsack_endpoint():
    candidates = [
        {
            "id": "ST-01", "name": "Station Alpha",
            "latitude": 20.2603, "longitude": 85.8395,
            "installation_cost": 100000, "expected_value": 70, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        },
        {
            "id": "ST-02", "name": "Station Beta",
            "latitude": 20.2961, "longitude": 85.8245,
            "installation_cost": 150000, "expected_value": 90, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        },
        {
            "id": "ST-03", "name": "Station Gamma",
            "latitude": 20.3533, "longitude": 85.8198,
            "installation_cost": 80000, "expected_value": 60, "coverage_score": 1.0,
            "feeder_connection_cost": 0, "is_user_cost": True
        }
    ]
    # Budget = 200,000 -> Should select Alpha (100k, 70) + Gamma (80k, 60) = 180k, 130 pts
    resp = client.post("/api/knapsack", json={"candidates": candidates, "budget": 200000})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_installation_cost"] <= 200000
    assert len(data["selected_stations"]) == 2
    assert data["total_value_benefit"] == 130
    assert data["remaining_budget"] == 20000
    assert len(data["rejected_stations"]) == 1
    assert data["rejected_stations"][0]["station"]["id"] == "ST-02"

