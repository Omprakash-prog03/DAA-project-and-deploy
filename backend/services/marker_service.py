"""
SQLite-backed persistent marker storage for the EV Planning map.

Markers are shared across all users: anyone can view them, and the
deployer can add / edit / delete annotations (candidate stations,
observation points, notes) that persist on the server.
"""
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

# Persist markers in the project data directory
_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "markers.db"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS markers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    latitude    REAL    NOT NULL,
    longitude   REAL    NOT NULL,
    note        TEXT    NOT NULL DEFAULT '',
    color       TEXT    NOT NULL DEFAULT '#F59E42',
    icon        TEXT    NOT NULL DEFAULT '📍',
    created_by  TEXT    NOT NULL DEFAULT 'anonymous',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_markers_lat ON markers(latitude);
CREATE INDEX IF NOT EXISTS idx_markers_lon ON markers(longitude);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock, _get_conn() as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


def add_marker(
    name: str,
    latitude: float,
    longitude: float,
    note: str = "",
    color: str = "#F59E42",
    icon: str = "📍",
    created_by: str = "anonymous",
) -> Dict[str, Any]:
    init_db()
    with _lock, _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO markers (name, latitude, longitude, note, color, icon, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, latitude, longitude, note, color, icon, created_by),
        )
        conn.commit()
        marker_id = cur.lastrowid
    return get_marker(marker_id)


def get_marker(marker_id: int) -> Optional[Dict[str, Any]]:
    with _lock, _get_conn() as conn:
        row = conn.execute("SELECT * FROM markers WHERE id = ?", (marker_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_markers() -> List[Dict[str, Any]]:
    with _lock, _get_conn() as conn:
        rows = conn.execute("SELECT * FROM markers ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def update_marker(marker_id: int, **fields: Any) -> Optional[Dict[str, Any]]:
    allowed = {"name", "note", "color", "icon"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_marker(marker_id)
    init_db()
    with _lock, _get_conn() as conn:
        cols = ", ".join(f"{k} = ?" for k in updates)
        cur = conn.execute(
            f"UPDATE markers SET {cols} WHERE id = ?",
            (*updates.values(), marker_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
    return get_marker(marker_id)


def delete_marker(marker_id: int) -> bool:
    with _lock, _get_conn() as conn:
        cur = conn.execute("DELETE FROM markers WHERE id = ?", (marker_id,))
        conn.commit()
    return cur.rowcount > 0


def clear_all_markers() -> int:
    with _lock, _get_conn() as conn:
        cur = conn.execute("DELETE FROM markers")
        conn.commit()
    return cur.rowcount


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "note": row["note"],
        "color": row["color"],
        "icon": row["icon"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }
