"""Shared pytest fixtures and environment detection."""
import socket
import ssl

import pytest

# External geo APIs used by the backend (Nominatim, Open Charge Map, OSRM,
# OpenRouteService, Overpass). Tests marked with @pytest.mark.external_api
# are skipped automatically when these are unreachable (e.g. restricted CI).
_EXTERNAL_HOSTS = [
    "nominatim.openstreetmap.org",
    "api.openchargemap.io",
    "router.project-osrm.org",
]


def _can_reach(host: str, port: int = 443, timeout: float = 4.0) -> bool:
    """Returns True only if a full TCP + TLS handshake succeeds."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.settimeout(timeout)
                ssock.do_handshake()
        return True
    except (OSError, ssl.SSLError):
        return False


EXTERNAL_API_AVAILABLE = any(_can_reach(host) for host in _EXTERNAL_HOSTS)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "external_api: requires live external geo APIs (skipped offline)"
    )


def pytest_collection_modifyitems(config, items):
    if EXTERNAL_API_AVAILABLE:
        return
    skip_offline = pytest.mark.skip(reason="External geo APIs unreachable (offline mode)")
    for item in items:
        if "external_api" in item.keywords:
            item.add_marker(skip_offline)
