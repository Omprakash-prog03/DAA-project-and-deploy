from dataclasses import dataclass

@dataclass(frozen=True)
class Station:
    """Represents a candidate EV charging station proposal."""
    id: str
    name: str
    location_id: str
    installation_cost: int
    expected_coverage: int
    capacity_kw: int
    priority: int
    demand_score: float

    def __post_init__(self):
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Station id must be a non-empty string.")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Station name must be a non-empty string.")
        if not self.location_id or not isinstance(self.location_id, str):
            raise ValueError("Station location_id must be a non-empty string.")
        if self.installation_cost <= 0:
            raise ValueError(f"Station {self.id} installation_cost must be > 0 (got {self.installation_cost}).")
        if self.expected_coverage < 0:
            raise ValueError(f"Station {self.id} expected_coverage cannot be negative.")
        if self.capacity_kw <= 0:
            raise ValueError(f"Station {self.id} capacity_kw must be > 0.")
        if self.priority not in (1, 2, 3):
            raise ValueError(f"Station {self.id} priority must be 1 (Standard), 2 (High), or 3 (Critical).")
        if self.demand_score < 0:
            raise ValueError(f"Station {self.id} demand_score cannot be negative.")

@dataclass(frozen=True)
class KnapsackItem:
    """Calculated knapsack item with real costs and integer benefit value."""
    station: Station
    weight: int
    value: int
    feeder_km: float
    feeder_cost: int

