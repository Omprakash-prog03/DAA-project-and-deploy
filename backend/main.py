import os
from pathlib import Path
from typing import Callable, Dict, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.config import settings
from backend.api import (
    geocode_router,
    stations_router,
    routing_router,
    optimization_router,
    markers_router,
)

app = FastAPI(
    title="EV Charging Station Placement & Route Planning",
    description="Real Geographic Data + Hand-Written DAA Algorithms (Kruskal, Dijkstra, 0/1 Knapsack)",
    version="2.0.0"
)


# ----------------------------------------------------------------------
# Security middleware
# ----------------------------------------------------------------------

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
        "img-src 'self' data: blob: https://*.google.com https://*.basemaps.cartocdn.com "
        "https://*.tile.openstreetmap.org; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "connect-src 'self' https://*.google.com https://*.basemaps.cartocdn.com "
        "https://*.tile.openstreetmap.org https://unpkg.com; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    ),
}


class SecurityHeadersMiddleware:
    """Attaches defensive security headers to every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in SECURITY_HEADERS.items():
                    headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RequestBodyTooLarge(Exception):
    """Raised internally when a request body exceeds the configured limit."""


class BodySizeLimitMiddleware:
    """Rejects HTTP requests whose body exceeds MAX_REQUEST_BYTES."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Fast rejection based on the Content-Length header.
        content_length = 0
        for key, value in scope.get("headers", []):
            if key == b"content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    pass
        if content_length > self.max_bytes:
            response = JSONResponse(
                {"detail": "Request body too large."},
                status_code=413,
            )
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> dict:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                received += len(body)
                if received > self.max_bytes:
                    raise RequestBodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestBodyTooLarge:
            response = JSONResponse(
                {"detail": "Request body too large."},
                status_code=413,
            )
            await response(scope, receive, send)


class RateLimitMiddleware:
    """Simple fixed-window per-IP rate limiter for configurable path prefixes."""

    def __init__(self, app: ASGIApp, limits: Dict[str, Tuple[int, int]]) -> None:
        self.app = app
        self.limits = limits
        self._buckets: Dict[Tuple[str, str], Tuple[float, int]] = {}

    def _client_ip(self, scope: Scope) -> str:
        # Prefer the left-most X-Forwarded-For entry when present.
        for key, value in scope.get("headers", []):
            if key == b"x-forwarded-for":
                parts = str(value).split(",")
                return parts[0].strip() or (scope.get("client") or ("unknown", 0))[0]
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _match(self, path: str) -> Tuple[int, int]:
        for prefix, limit in self.limits.items():
            if path.startswith(prefix):
                return limit
        return (0, 0)

    def _check(self, ip: str, path: str, now: float) -> bool:
        max_requests, window = self._match(path)
        if max_requests <= 0:
            return True

        key = (ip, path)
        start, count = self._buckets.get(key, (now, 0))
        if now - start >= window:
            # New window
            self._buckets[key] = (now, 1)
        elif count < max_requests:
            self._buckets[key] = (start, count + 1)
        else:
            return False

        # Opportunistic cleanup of stale buckets.
        if len(self._buckets) > 10_000:
            self._buckets = {
                k: v for k, v in self._buckets.items() if now - v[0] < window
            }
        return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time

        now = time.monotonic()
        if not self._check(self._client_ip(scope), scope.get("path", ""), now):
            response = JSONResponse(
                {"detail": "Rate limit exceeded. Please slow down."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


# ----------------------------------------------------------------------
# Middleware stack (outermost first)
# ----------------------------------------------------------------------

app.add_middleware(RateLimitMiddleware, limits=settings.rate_limit_map)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_BYTES)
app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS only for explicitly configured origins (no wildcard).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Register API Routers
app.include_router(geocode_router)
app.include_router(stations_router)
app.include_router(routing_router)
app.include_router(optimization_router)
app.include_router(markers_router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Returns real API connectivity and environment configuration status."""
    return {
        "status": "healthy",
        "openchargemap_key_configured": bool(settings.OPENCHARGEMAP_API_KEY),
        "openrouteservice_key_configured": bool(settings.OPENROUTESERVICE_API_KEY),
        "routing_engine": "OpenRouteService" if settings.OPENROUTESERVICE_API_KEY else "OpenStreetMap OSRM",
        "algorithms": [
            "Kruskal's Minimum Spanning Tree (Hand-written)",
            "Dijkstra's Shortest Path (Hand-written)",
            "0/1 Knapsack Dynamic Programming (Hand-written)"
        ]
    }


# Mount Frontend Static Directory
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir, html=False), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False
    )
