import logging
from collections import OrderedDict
from typing import Optional, Dict

import requests
from fastapi import HTTPException

from backend.config import settings
from backend.models.route import GeocodeResult

logger = logging.getLogger(__name__)


class _BoundedLRUCache:
    """Simple bounded LRU cache to prevent unbounded memory growth."""

    def __init__(self, max_size: int):
        self.max_size = max(1, max_size)
        self._store: OrderedDict[str, GeocodeResult] = OrderedDict()

    def get(self, key: str) -> Optional[GeocodeResult]:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: str, value: GeocodeResult) -> None:
        self._store[key] = value
        self._store.move_to_end(key)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)


# In-memory LRU cache to avoid excessive external requests (bounded)
_geocode_cache: _BoundedLRUCache = _BoundedLRUCache(settings.GEOCODE_CACHE_SIZE)


def geocode_location(query: str) -> GeocodeResult:
    """
    Geocodes a location query (e.g. 'Bhubaneswar', 'Delhi', 'New York')
    using real OpenStreetMap Nominatim or OpenRouteService geocoding.
    """
    clean_query = query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    if len(clean_query) > settings.MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Search query too long (max {settings.MAX_QUERY_LENGTH} characters).",
        )

    cache_key = clean_query.lower()
    cached = _geocode_cache.get(cache_key)
    if cached is not None:
        return cached

    # 1. Try OpenRouteService if API key configured
    if settings.OPENROUTESERVICE_API_KEY:
        try:
            ors_url = "https://api.openrouteservice.org/geocode/search"
            headers = {
                "Authorization": settings.OPENROUTESERVICE_API_KEY,
                "User-Agent": settings.USER_AGENT,
            }
            params = {"text": clean_query, "size": 1}
            r = requests.get(ors_url, params=params, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    label = feat.get("properties", {}).get("label", clean_query)
                    if len(coords) >= 2:
                        res = GeocodeResult(
                            query=clean_query,
                            display_name=label,
                            latitude=float(coords[1]),
                            longitude=float(coords[0]),
                            data_source="HeiGIT / OpenRouteService Geocoding",
                        )
                        _geocode_cache.set(cache_key, res)
                        return res
        except Exception as exc:  # noqa: BLE001 - fall through to Nominatim
            logger.warning("OpenRouteService geocoding failed: %s", exc)

    # 2. OpenStreetMap Nominatim (Standard OpenStreetMap Geocoder)
    try:
        nom_url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }
        params = {
            "q": clean_query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        resp = requests.get(nom_url, params=params, headers=headers, timeout=8)

        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Geocoding service returned HTTP {resp.status_code}.",
            )

        data = resp.json()
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No geographic location found for query '{clean_query}'. Please verify spelling or try a nearby city.",
            )

        item = data[0]
        bbox = [float(b) for b in item.get("boundingbox", [])] if "boundingbox" in item else None

        result = GeocodeResult(
            query=clean_query,
            display_name=item.get("display_name", clean_query),
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            bounding_box=bbox,
            data_source="OpenStreetMap Nominatim",
        )
        _geocode_cache.set(cache_key, result)
        return result

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Geocoding request timed out. Please check your internet connection and try again.",
        )
    except requests.exceptions.RequestException:
        # Do not leak internal network exception details to the client.
        logger.error("Network error communicating with geocoding provider", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Network error communicating with geocoding provider. Please try again later.",
        )
