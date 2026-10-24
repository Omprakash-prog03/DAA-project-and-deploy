from fastapi import APIRouter, HTTPException
from backend.models.route import (
    RouteRequest,
    RouteResponse,
    DistanceMatrixRequest,
    DistanceMatrixResponse,
)
from backend.services.routing_service import get_real_road_distance_matrix, get_real_route_geometry

router = APIRouter(prefix="/api", tags=["Routing & Distances"])

@router.post("/distance-matrix", response_model=DistanceMatrixResponse)
def compute_distance_matrix_endpoint(req: DistanceMatrixRequest):
    """Computes the full NxN road distance matrix over real OpenStreetMap road networks."""
    if len(req.locations) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinate locations required.")
    return get_real_road_distance_matrix(req.locations)

@router.post("/route", response_model=RouteResponse)
def get_route_geometry_endpoint(req: RouteRequest):
    """Retrieves real turn-by-turn driving road geometry between two points."""
    return get_real_route_geometry(
        start_lat=req.start_lat,
        start_lon=req.start_lon,
        end_lat=req.end_lat,
        end_lon=req.end_lon
    )

