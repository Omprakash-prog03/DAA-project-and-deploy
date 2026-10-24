from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """System-wide configuration parameters."""
    total_budget: int = 500_000
    coverage_threshold_km: float = 5.0
    feeder_cost_per_km: int = 25_000
    include_backbone_in_budget: bool = False
    coverage_weight: float = 10.0
    capacity_weight: float = 0.1
    priority_bonus_multiplier: float = 15.0
    demand_weight: float = 5.0
    max_dp_cells: int = 200_000

    def __post_init__(self):
        if self.total_budget < 0:
            raise ValueError(f"total_budget must be >= 0 (got {self.total_budget}).")
        if self.coverage_threshold_km <= 0:
            raise ValueError(f"coverage_threshold_km must be > 0 (got {self.coverage_threshold_km}).")
        if self.feeder_cost_per_km < 0:
            raise ValueError(f"feeder_cost_per_km cannot be negative (got {self.feeder_cost_per_km}).")
        if self.max_dp_cells <= 0:
            raise ValueError(f"max_dp_cells must be > 0 (got {self.max_dp_cells}).")

