from fastapi import APIRouter, Query, HTTPException
from typing import List
from backend.models.station import EVChargingStation
from backend.services.openchargemap_service import fetch_real_charging_stations
from backend.utils.validation import validate_coordinates

router = APIRouter(prefix="/api/charging-stations", tags=["Charging Stations"])

@router.get("", response_model=List[EVChargingStation])
def get_charging_stations_endpoint(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius: float = Query(25.0, gt=0.0, le=100.0, description="Search radius in kilometers"),
    max_results: int = Query(30, ge=1, le=100)
):
    """
    Retrieves real EV charging stations from Open Charge Map API.
    If no stations are found, returns an empty list (never fake data).
    """
    if not validate_coordinates(lat, lon):
        raise HTTPException(status_code=400, detail="Invalid geographic coordinates.")
    
    stations = fetch_real_charging_stations(
        latitude=lat,
        longitude=lon,
        radius_km=radius,
        max_results=max_results
    )
    return stations

