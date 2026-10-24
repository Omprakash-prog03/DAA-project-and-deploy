from pydantic import BaseModel, Field
from typing import List, Optional

class ConnectorInfo(BaseModel):
    title: str = "Standard Charger"
    type_name: Optional[str] = None
    power_kw: Optional[float] = None
    quantity: Optional[int] = 1

class EVChargingStation(BaseModel):
    """Real charging station directly returned from Open Charge Map / OpenStreetMap."""
    id: str
    name: str
    latitude: float
    longitude: float
    address: str = "Address not listed"
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    operator: str = "Independent / Unknown"
    connectors: List[ConnectorInfo] = Field(default_factory=list)
    number_of_points: int = 1
    data_source: str = "Open Charge Map"  # or "OpenStreetMap"

class CandidateStation(BaseModel):
    """
    Candidate station selected by user for DAA planning.
    Clear separation: Geographic fields come from real API;
    Planning costs and benefit values are user-entered or explicitly configured.
    """
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    installation_cost: int = Field(
        ..., gt=0, le=100_000_000,
        description="User-entered installation cost in INR"
    )
    expected_value: int = Field(
        ..., gt=0, le=1_000_000,
        description="User-entered public benefit value score"
    )
    coverage_score: float = Field(default=1.0, ge=0.0, le=10.0, description="Demographic demand multiplier")
    feeder_connection_cost: int = Field(default=0, ge=0, le=100_000_000, description="Derived from shortest incident MST edge")
    operator: Optional[str] = Field(default=None, max_length=200)
    is_user_cost: bool = True

