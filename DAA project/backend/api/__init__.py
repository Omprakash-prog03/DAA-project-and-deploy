from backend.api.geocode import router as geocode_router
from backend.api.charging_stations import router as stations_router
from backend.api.routing import router as routing_router
from backend.api.optimization import router as optimization_router
from backend.api.markers import router as markers_router

__all__ = [
    "geocode_router",
    "stations_router",
    "routing_router",
    "optimization_router",
    "markers_router",
]

