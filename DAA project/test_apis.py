import requests
import json

def test_nominatim():
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "EV-Placement-DAA-Academic/1.0 (contact@univ.edu)"}
    params = {"q": "Bhubaneswar", "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers=headers)
    print("Nominatim status:", r.status_code)
    if r.status_code == 200 and r.json():
        loc = r.json()[0]
        print("Geocoded:", loc["display_name"], "lat:", loc["lat"], "lon:", loc["lon"])
        return float(loc["lat"]), float(loc["lon"])
    return None, None

def test_overpass(lat, lon):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="charging_station"](around:25000, {lat}, {lon});
      way["amenity"="charging_station"](around:25000, {lat}, {lon});
    );
    out center 20;
    """
    headers = {
        "User-Agent": "EV-Placement-DAA-Academic/1.0 (contact@univ.edu)",
        "Accept": "application/json",
    }
    r = requests.post(url, data=query, headers=headers)
    print("Overpass status:", r.status_code)
    if r.status_code == 200:
        elements = r.json().get("elements", [])
        print("Found real EV charging stations in OSM:", len(elements))
        for el in elements[:3]:
            tags = el.get("tags", {})
            name = tags.get("name", "EV Charging Point")
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            print(" -", name, el_lat, el_lon, tags.get("operator", "Unknown Operator"))

def test_osrm_route():
    # Public OSRM API (OpenStreetMap road routing)
    url = "http://router.project-osrm.org/route/v1/driving/85.8245,20.2961;85.8345,20.3061?overview=full&geometries=geojson"
    r = requests.get(url, headers={"User-Agent": "EV-Placement-DAA-Academic/1.0"})
    print("OSRM route status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        routes = data.get("routes", [])
        if routes:
            print("OSRM distance (meters):", routes[0]["distance"], "duration (s):", routes[0]["duration"])

if __name__ == "__main__":
    lat, lon = test_nominatim()
    if lat and lon:
        test_overpass(lat, lon)
    test_osrm_route()
