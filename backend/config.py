import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read an integer env var clamped to [minimum, maximum]."""
    try:
        raw = int(str(os.getenv(name, str(default))).strip())
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, raw))


class Settings:
    OPENCHARGEMAP_API_KEY: str = os.getenv("OPENCHARGEMAP_API_KEY", "").strip()
    OPENROUTESERVICE_API_KEY: str = (
        os.getenv("OPENROUTESERVICE_API_KEY", "").strip() or
        os.getenv("HEIGIT_API_KEY", "").strip()
    )
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0").strip()
    APP_PORT: int = _env_int("APP_PORT", 8085, 1, 65535)
    USER_AGENT: str = "EV-Placement-DAA-Academic/1.0 (contact: student@academic.edu)"

    # ------------------------------------------------------------------
    # Security configuration
    # ------------------------------------------------------------------
    # Comma-separated list of allowed CORS origins. Defaults to the local
    # app origins only (the frontend is served same-origin by this app, so
    # cross-origin access is not required in normal operation).
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8085,http://127.0.0.1:8085",
    ).strip()

    # Per-IP rate limits: "path_prefix:max_requests:window_seconds"
    RATE_LIMITS: str = os.getenv(
        "RATE_LIMITS",
        "/api/geocode:30:60,/api/charging-stations:20:60,"
        "/api/mst:15:60,/api/dijkstra:15:60,/api/knapsack:30:60,"
        "/api/distance-matrix:15:60,/api/route:15:60",
    ).strip()

    # Maximum request body size in bytes for JSON API requests (2 MB).
    MAX_REQUEST_BYTES: int = _env_int("MAX_REQUEST_BYTES", 2 * 1024 * 1024, 1024, 16 * 1024 * 1024)

    # ------------------------------------------------------------------
    # Input bounds (defense against resource-exhaustion / DoS)
    # ------------------------------------------------------------------
    MAX_STATIONS_PER_REQUEST: int = _env_int("MAX_STATIONS_PER_REQUEST", 30, 2, 100)
    MAX_MATRIX_LOCATIONS: int = _env_int("MAX_MATRIX_LOCATIONS", 25, 2, 50)
    MAX_KNAPSACK_CANDIDATES: int = _env_int("MAX_KNAPSACK_CANDIDATES", 200, 1, 1000)
    MAX_BUDGET: int = _env_int("MAX_BUDGET", 1_000_000_000, 0, 10_000_000_000)
    MAX_QUERY_LENGTH: int = _env_int("MAX_QUERY_LENGTH", 200, 1, 500)
    MAX_NAME_LENGTH: int = _env_int("MAX_NAME_LENGTH", 200, 1, 500)
    MAX_ID_LENGTH: int = _env_int("MAX_ID_LENGTH", 100, 1, 500)

    # Geocoding cache bound (LRU) to prevent unbounded memory growth.
    GEOCODE_CACHE_SIZE: int = _env_int("GEOCODE_CACHE_SIZE", 200, 1, 1000)

    @property
    def cors_origin_list(self) -> list:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return origins or ["http://localhost:8085", "http://127.0.0.1:8085"]

    @property
    def rate_limit_map(self) -> dict:
        limits = {}
        for entry in self.RATE_LIMITS.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) != 3:
                continue
            prefix, max_req, window = parts[0].strip(), parts[1], parts[2]
            try:
                limits[prefix] = (int(max_req), int(window))
            except ValueError:
                continue
        return limits


settings = Settings()
