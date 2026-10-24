from pydantic import BaseModel, Field
from typing import Optional


class MarkerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    note: str = Field(default="", max_length=1000)
    color: str = Field(default="#F59E42", max_length=20)
    icon: str = Field(default="📍", max_length=10)
    created_by: str = Field(default="anonymous", max_length=100)


class MarkerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    note: Optional[str] = Field(default=None, max_length=1000)
    color: Optional[str] = Field(default=None, max_length=20)
    icon: Optional[str] = Field(default=None, max_length=10)


class Marker(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    note: str = ""
    color: str = "#F59E42"
    icon: str = "📍"
    created_by: str = "anonymous"
    created_at: str = ""
