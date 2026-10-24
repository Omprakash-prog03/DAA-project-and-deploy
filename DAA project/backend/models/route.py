from pydantic import BaseModel, Field
from typing import List, Optional


class Coordinates(BaseModel):
    """Geographic coordinate with strict range validation (WGS-84)."""
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class GeocodeResult(BaseModel):
    query: str
    display_name: str
    latitude: float
    longitude: float
    bounding_box: Optional[List[float]] = None
    data_source: str = "OpenStreetMap Nominatim"


class RouteRequest(BaseModel):
    start_lat: float = Field(..., ge=-90.0, le=90.0)
    start_lon: float = Field(..., ge=-180.0, le=180.0)
    end_lat: float = Field(..., ge=-90.0, le=90.0)
    end_lon: float = Field(..., ge=-180.0, le=180.0)
    start_name: Optional[str] = Field(default="Origin", max_length=200)
    end_name: Optional[str] = Field(default="Destination", max_length=200)


class RouteResponse(BaseModel):
    distance_km: float
    duration_min: float
    geometry_geojson: Optional[List[List[float]]] = None  # [[lon, lat], ...]
    data_source: str = "OpenStreetMap OSRM / OpenRouteService"


class DistanceMatrixRequest(BaseModel):
    locations: List[Coordinates] = Field(..., min_length=2, max_length=50)


class DistanceMatrixResponse(BaseModel):
    distances_km: List[List[float]]
    durations_min: List[List[float]]
    data_source: str
