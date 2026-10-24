from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class Road:
    """Represents an undirected road segment connecting two locations."""
    id: str
    u: str
    v: str
    distance_km: float

    def __post_init__(self):
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Road id must be a non-empty string.")
        if not self.u or not self.v:
            raise ValueError(f"Road {self.id} must connect two valid locations.")
        if self.u == self.v:
            raise ValueError(f"Self-loop detected on road {self.id}: endpoints cannot be identical ({self.u}).")
        if self.distance_km <= 0:
            raise ValueError(f"Road {self.id} distance must be strictly positive (got {self.distance_km}).")

    @property
    def canonical_endpoints(self) -> Tuple[str, str]:
        """Returns ordered endpoint pair for undirected comparison."""
        return (self.u, self.v) if self.u <= self.v else (self.v, self.u)

