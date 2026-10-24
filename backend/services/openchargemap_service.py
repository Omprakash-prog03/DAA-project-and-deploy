import requests
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from backend.config import settings
from backend.models.station import EVChargingStation, ConnectorInfo

def fetch_real_charging_stations(
    latitude: float,
    longitude: float,
    radius_km: float = 25.0,
    max_results: int = 30
) -> List[EVChargingStation]:
    """
    Retrieves real EV charging stations from Open Charge Map API.
    If no API key is set or zero results are returned, transparently queries
    OpenStreetMap Overpass API for verified physical charging infrastructure.
    
    IMPORTANT: Never returns synthetic, hardcoded or fake stations.
    """
    stations: List[EVChargingStation] = []

    # 1. Query Open Charge Map API if key is available
    if settings.OPENCHARGEMAP_API_KEY:
        try:
            ocm_url = "https://api.openchargemap.io/v3/poi/"
            headers = {
                "X-API-Key": settings.OPENCHARGEMAP_API_KEY,
                "User-Agent": settings.USER_AGENT
            }
            params = {
                "output": "json",
                "latitude": latitude,
                "longitude": longitude,
                "distance": radius_km,
                "distanceunit": "km",
                "maxresults": max_results,
                "compact": "true",
                "verbose": "false"
            }
            resp = requests.get(ocm_url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    addr_info = item.get("AddressInfo", {})
                    lat = addr_info.get("Latitude")
                    lon = addr_info.get("Longitude")
                    if lat is None or lon is None:
                        continue

                    # Extract operator
                    op_info = item.get("OperatorInfo", {}) or {}
                    operator_name = op_info.get("Title") or "Independent / Private Operator"

                    # Extract connectors
                    connections = []
                    for conn in item.get("Connections", []) or []:
                        conn_type = conn.get("ConnectionType", {}) or {}
                        connections.append(ConnectorInfo(
                            title=conn_type.get("Title", "Standard EV Charger"),
                            type_name=conn_type.get("FormalName"),
                            power_kw=conn.get("PowerKW"),
                            quantity=conn.get("Quantity", 1)
                        ))

                    stations.append(EVChargingStation(
                        id=f"OCM-{item.get('ID')}",
                        name=addr_info.get("Title", f"EV Station #{item.get('ID')}"),
                        latitude=float(lat),
                        longitude=float(lon),
                        address=addr_info.get("AddressLine1") or addr_info.get("AddressLine2") or "Road network waypoint",
                        city=addr_info.get("Town"),
                        state=addr_info.get("StateOrProvince"),
                        country=addr_info.get("Country", {}).get("Title"),
                        operator=operator_name,
                        connectors=connections,
                        number_of_points=item.get("NumberOfPoints") or len(connections) or 1,
                        data_source="Open Charge Map API"
                    ))
                if stations:
                    return stations
        except Exception:
            pass  # Fall through to OpenStreetMap verified data

    # 2. Query Live OpenStreetMap Overpass API for real charging stations
    #    Try multiple Overpass endpoints for reliability
    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.osm.ch/api/interpreter",
    ]

    radius_meters = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="charging_station"](around:{radius_meters}, {latitude:.6f}, {longitude:.6f});
      way["amenity"="charging_station"](around:{radius_meters}, {latitude:.6f}, {longitude:.6f});
    );
    out center {max_results};
    """
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Accept": "application/json"
    }

    for overpass_url in overpass_endpoints:
        try:
            resp = requests.post(overpass_url, data=query, headers=headers, timeout=25)
            if resp.status_code == 200:
                osm_data = resp.json()
                elements = osm_data.get("elements", [])
                for el in elements:
                    tags = el.get("tags", {})
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat is None or lon is None:
                        continue

                    name = tags.get("name") or tags.get("operator") or f"OSM EV Hub #{el.get('id')}"
                    operator = tags.get("operator") or tags.get("brand") or "Public Charging Infrastructure"
                    socket_type = tags.get("socket:type2") or tags.get("socket:chademo") or tags.get("socket:type2_combo")
                    capacity = tags.get("capacity")
                    try:
                        num_pts = int(capacity) if capacity else 1
                    except ValueError:
                        num_pts = 1

                    conns = [ConnectorInfo(
                        title=socket_type or "Universal EV Connector",
                        power_kw=None,
                        quantity=num_pts
                    )]

                    stations.append(EVChargingStation(
                        id=f"OSM-{el.get('id')}",
                        name=name,
                        latitude=float(lat),
                        longitude=float(lon),
                        address=tags.get("addr:street") or tags.get("addr:city") or "Geographic Coordinate Waypoint",
                        city=tags.get("addr:city"),
                        state=tags.get("addr:state"),
                        country=tags.get("addr:country"),
                        operator=operator,
                        connectors=conns,
                        number_of_points=num_pts,
                        data_source="OpenStreetMap (Overpass Infrastructure API)"
                    ))
                if stations:
                    return stations
        except Exception:
            continue  # Try next Overpass endpoint

    return stations

