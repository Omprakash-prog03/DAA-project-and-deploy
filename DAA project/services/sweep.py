from typing import List, Dict, Any
from models.graph import Graph
from models.station import Station
from models.config import Config
from services.optimization import run_full_pipeline

def run_budget_sweep(
    graph: Graph,
    candidate_stations: List[Station],
    base_config: Config,
    steps: int = 12
) -> List[Dict[str, Any]]:
    """
    Parametric budget sweep re-running the full optimization pipeline across varied budgets.
    Powers the dynamic Coverage vs Budget chart on the Dashboard.
    """
    if base_config.total_budget <= 0:
        return []

    # Sweep from 20% to 160% of current budget
    min_budget = int(base_config.total_budget * 0.20)
    max_budget = int(base_config.total_budget * 1.60)
    step_size = max(10000, (max_budget - min_budget) // max(1, steps - 1))

    sweep_results: List[Dict[str, Any]] = []

    for b in range(min_budget, max_budget + step_size, step_size):
        # Override budget in config
        test_config = Config(
            total_budget=b,
            coverage_threshold_km=base_config.coverage_threshold_km,
            feeder_cost_per_km=base_config.feeder_cost_per_km,
            include_backbone_in_budget=base_config.include_backbone_in_budget,
            coverage_weight=base_config.coverage_weight,
            capacity_weight=base_config.capacity_weight,
            priority_bonus_multiplier=base_config.priority_bonus_multiplier,
            demand_weight=base_config.demand_weight,
            max_dp_cells=base_config.max_dp_cells
        )
        opt_res = run_full_pipeline(graph, candidate_stations, test_config)
        sweep_results.append({
            "budget": b,
            "coverage_pct": opt_res.coverage_percentage,
            "stations_selected": len(opt_res.knapsack_result.selected_items),
            "efficiency_score": opt_res.efficiency_score,
            "total_value": opt_res.knapsack_result.total_value,
        })

    return sweep_results

