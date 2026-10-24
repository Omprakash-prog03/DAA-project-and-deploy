from dataclasses import dataclass

@dataclass(frozen=True)
class Location:
    """Represents a physical road network waypoint or intersection."""
    id: str
    name: str
    x: float
    y: float
    is_important: bool = True
    demand_factor: float = 1.0

    def __post_init__(self):
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Location id must be a non-empty string.")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Location name must be a non-empty string.")
        if self.demand_factor <= 0:
            raise ValueError(f"demand_factor for {self.id} must be strictly positive.")

