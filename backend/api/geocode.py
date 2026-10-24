from fastapi import APIRouter, Query, HTTPException
from backend.models.route import GeocodeResult
from backend.services.geocoding_service import geocode_location
from backend.config import settings

router = APIRouter(prefix="/api/geocode", tags=["Geocoding"])


def _sanitize_query(query: str) -> str:
    """Strip and cap the geocoding query; reject control characters."""
    clean = query.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    if len(clean) > settings.MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Search query too long (max {settings.MAX_QUERY_LENGTH} characters).",
        )
    if any(ord(ch) < 32 for ch in clean):
        raise HTTPException(status_code=422, detail="Search query contains invalid characters.")
    return clean


@router.get("", response_model=GeocodeResult)
def geocode_endpoint(q: str = Query(..., min_length=2, description="City or location query")):
    """Geocodes a geographic address or city into real latitude and longitude."""
    clean_query = _sanitize_query(q)
    return geocode_location(clean_query)
