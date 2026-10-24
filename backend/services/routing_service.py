import requests
from typing import List, Dict, Tuple, Optional
from fastapi import HTTPException

from backend.config import settings
from backend.models.route import Coordinates, RouteResponse, DistanceMatrixResponse
from backend.utils.distance import haversine_distance_km


def get_real_road_distance_matrix(locations: List[Coordinates]) -> DistanceMatrixResponse:
    """
    Computes real road-network distance matrix between all coordinate pairs.
    Uses OpenRouteService (HeiGIT) or Open Source Routing Machine (OSRM).
    """
    n = len(locations)
    if n == 0:
        return DistanceMatrixResponse(distances_km=[], durations_min=[], data_source="Empty")
    if n == 1:
        return DistanceMatrixResponse(distances_km=[[0.0]], durations_min=[[0.0]], data_source="Single Point")

    # Bound the matrix size: each additional location triggers n external
    # routing-API calls, so unbounded input allows resource exhaustion.
    if n > settings.MAX_MATRIX_LOCATIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Distance matrix supports at most {settings.MAX_MATRIX_LOCATIONS} locations.",
        )

    # 1. Try OpenRouteService Matrix API if API key is provided
    if settings.OPENROUTESERVICE_API_KEY:
        try:
            ors_url = "https://api.openrouteservice.org/v2/matrix/driving-car"
            headers = {
                "Authorization": settings.OPENROUTESERVICE_API_KEY,
                "Content-Type": "application/json",
                "User-Agent": settings.USER_AGENT
            }
            # ORS coordinates are [lon, lat]
            coords = [[loc.lon, loc.lat] for loc in locations]
            body = {
                "locations": coords,
                "metrics": ["distance", "duration"]
            }
            resp = requests.post(ors_url, json=body, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                raw_distances = data.get("distances", [])
                raw_durations = data.get("durations", [])
                
                # Convert meters to km and seconds to minutes
                distances_km = [
                    [round(d / 1000.0, 3) if d is not None else 0.0 for d in row]
                    for row in raw_distances
                ]
                durations_min = [
                    [round(t / 60.0, 2) if t is not None else 0.0 for t in row]
                    for row in raw_durations
                ]
                return DistanceMatrixResponse(
                    distances_km=distances_km,
                    durations_min=durations_min,
                    data_source="HeiGIT / OpenRouteService Real Road Matrix"
                )
        except Exception:
            pass  # Fallback to OSRM

    # 2. Open Source Routing Machine (OSRM) on Live OpenStreetMap Road Network
    try:
        # Formulate coordinate string: lon1,lat1;lon2,lat2;...
        coords_str = ";".join(f"{loc.lon:.6f},{loc.lat:.6f}" for loc in locations)
        osrm_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance,duration"
        headers = {"User-Agent": settings.USER_AGENT}
        resp = requests.get(osrm_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            raw_distances = data.get("distances", [])
            raw_durations = data.get("durations", [])

            distances_km = [
                [round(d / 1000.0, 3) if d is not None else 0.0 for d in row]
                for row in raw_distances
            ]
            durations_min = [
                [round(t / 60.0, 2) if t is not None else 0.0 for t in row]
                for row in raw_durations
            ]
            return DistanceMatrixResponse(
                distances_km=distances_km,
                durations_min=durations_min,
                data_source="OpenStreetMap Road Network (OSRM Driving Engine)"
            )
    except Exception:
        pass

    # 3. Transparent Fallback: Haversine distance with explicit notice
    # Used only if all external routing servers are unreachable
    matrix_km = [[0.0] * n for _ in range(n)]
    durations = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d = haversine_distance_km(locations[i].lat, locations[i].lon, locations[j].lat, locations[j].lon)
                matrix_km[i][j] = d
                durations[i][j] = round((d / 40.0) * 60.0, 1)

    return DistanceMatrixResponse(
        distances_km=matrix_km,
        durations_min=durations,
        data_source="Haversine Direct Distance (External Routing Servers Offline)"
    )

def get_real_route_geometry(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
) -> RouteResponse:
    """
    Retrieves the actual turn-by-turn driving road geometry (GeoJSON coordinate array)
    from OpenRouteService or OSRM.
    """
    # 1. Try OpenRouteService Directions API if key configured
    if settings.OPENROUTESERVICE_API_KEY:
        try:
            ors_url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
            headers = {
                "Authorization": settings.OPENROUTESERVICE_API_KEY,
                "Content-Type": "application/json",
                "User-Agent": settings.USER_AGENT
            }
            body = {
                "coordinates": [[start_lon, start_lat], [end_lon, end_lat]]
            }
            resp = requests.post(ors_url, json=body, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    props = feat.get("properties", {}).get("summary", {})
                    dist_km = round(props.get("distance", 0) / 1000.0, 2)
                    dur_min = round(props.get("duration", 0) / 60.0, 1)
                    return RouteResponse(
                        distance_km=dist_km,
                        duration_min=dur_min,
                        geometry_geojson=coords,
                        data_source="HeiGIT / OpenRouteService Road Geometry"
                    )
        except Exception:
            pass

    # 2. OSRM Road Directions Engine
    try:
        osrm_url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{start_lon:.6f},{start_lat:.6f};{end_lon:.6f},{end_lat:.6f}"
            f"?overview=full&geometries=geojson"
        )
        headers = {"User-Agent": settings.USER_AGENT}
        resp = requests.get(osrm_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            routes = data.get("routes", [])
            if routes:
                route = routes[0]
                dist_km = round(route.get("distance", 0) / 1000.0, 2)
                dur_min = round(route.get("duration", 0) / 60.0, 1)
                coords = route.get("geometry", {}).get("coordinates", [])
                return RouteResponse(
                    distance_km=dist_km,
                    duration_min=dur_min,
                    geometry_geojson=coords,
                    data_source="OpenStreetMap Road Network (OSRM)"
                )
    except Exception:
        pass

    # Direct line fallback if routing servers are completely unavailable
    direct_km = haversine_distance_km(start_lat, start_lon, end_lat, end_lon)
    return RouteResponse(
        distance_km=direct_km,
        duration_min=round((direct_km / 40.0) * 60.0, 1),
        geometry_geojson=[[start_lon, start_lat], [end_lon, end_lat]],
        data_source="Straight-line Reference (Routing Service Offline)"
    )

