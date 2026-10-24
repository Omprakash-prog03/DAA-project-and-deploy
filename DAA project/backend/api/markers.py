from fastapi import APIRouter, HTTPException
from typing import List

from backend.models.marker import MarkerCreate, MarkerUpdate, Marker
from backend.services.marker_service import (
    add_marker,
    get_marker,
    list_markers,
    update_marker,
    delete_marker,
    clear_all_markers,
)

router = APIRouter(prefix="/api/markers", tags=["Map Markers"])


@router.get("", response_model=List[Marker])
def get_markers():
    """Returns all persistent markers visible to everyone."""
    return [Marker(**m) for m in list_markers()]


@router.post("", response_model=Marker, status_code=201)
def create_marker(req: MarkerCreate):
    """Adds a new persistent marker to the shared map."""
    return Marker(**add_marker(
        name=req.name,
        latitude=req.latitude,
        longitude=req.longitude,
        note=req.note,
        color=req.color,
        icon=req.icon,
        created_by=req.created_by,
    ))


@router.put("/{marker_id}", response_model=Marker)
def edit_marker(marker_id: int, req: MarkerUpdate):
    """Updates an existing marker (name, note, color, icon)."""
    marker = update_marker(marker_id, **req.model_dump(exclude_none=True))
    if marker is None:
        raise HTTPException(status_code=404, detail="Marker not found.")
    return Marker(**marker)


@router.delete("/{marker_id}")
def remove_marker(marker_id: int):
    """Deletes a marker from the shared map."""
    if not delete_marker(marker_id):
        raise HTTPException(status_code=404, detail="Marker not found.")
    return {"detail": "Marker deleted."}


@router.delete("")
def remove_all_markers():
    """Removes all markers (admin/owner action)."""
    count = clear_all_markers()
    return {"detail": f"{count} marker(s) deleted."}
