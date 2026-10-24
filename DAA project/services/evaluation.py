from typing import Dict, List, Any
from models.graph import Graph
from models.station import Station
from models.config import Config
from models.results import MSTResult, DijkstraResult, KnapsackResult, OptimizationResult

def synthesize_optimization(
    timestamp: str,
    config: Config,
    graph: Graph,
    mst_result: MSTResult,
    knapsack_result: KnapsackResult,
    dijkstra_result: DijkstraResult,
    covered_locations: List[str],
    uncovered_locations: List[str],
    all_stations: List[Station]
) -> OptimizationResult:
    """
    Synthesizes algorithm results into the final OptimizationResult dossier.
    Computes coverage percentages, finite distance averages, declared vs measured
    discrepancy, and the overall multi-objective efficiency score.
    """
    total_locations = max(1, len(graph.locations))
    coverage_pct = round((len(covered_locations) / total_locations) * 100.0, 1)

    # Important locations analysis
    important_locs = [lid for lid, loc in graph.locations.items() if loc.is_important]
    total_important = max(1, len(important_locs))
    covered_important_count = sum(1 for lid in covered_locations if graph.locations[lid].is_important)
    important_coverage_pct = round((covered_important_count / total_important) * 100.0, 1)

    # Distance metrics (strictly isolating finite values from inf)
    covered_distances = [
        dijkstra_result.distances[lid]
        for lid in covered_locations
        if dijkstra_result.distances[lid] < float('inf')
    ]
    avg_dist_covered = (
        round(sum(covered_distances) / len(covered_distances), 2)
        if covered_distances else 0.0
    )

    all_reachable_distances = [
        dist for dist in dijkstra_result.distances.values()
        if dist < float('inf')
    ]
    avg_dist_reachable = (
        round(sum(all_reachable_distances) / len(all_reachable_distances), 2)
        if all_reachable_distances else 0.0
    )
    max_dist = (
        round(max(all_reachable_distances), 2)
        if all_reachable_distances else 0.0
    )

    # Benefit value analysis
    total_available_value = sum(
        round(
            config.coverage_weight * s.expected_coverage
            + config.capacity_weight * s.capacity_kw
            + config.priority_bonus_multiplier * s.priority
            + config.demand_weight * s.demand_score
        )
        for s in all_stations
    )
    total_available_value = max(1, total_available_value)
    selected_value = knapsack_result.total_value

    # Capital efficiency (budget utilization)
    effective_budget = max(1, config.total_budget)
    budget_utilization = min(1.0, max(0.0, knapsack_result.total_weight / effective_budget))

    # Overall efficiency formula: Coverage% * (Val_sel / Val_tot) * Budget_utilization
    # Normalized to 0.0 - 100.0
    geo_reach = len(covered_locations) / total_locations
    val_capture = selected_value / total_available_value
    # Weighted geometric-mean style score
    raw_efficiency = (geo_reach * 0.45 + val_capture * 0.35 + budget_utilization * 0.20) * 100.0
    efficiency_score = round(raw_efficiency, 1)

    # Declared vs Measured Coverage Comparison
    selected_candidates = [it.station for it in knapsack_result.selected_items]
    declared_total_reach = sum(s.expected_coverage for s in selected_candidates)
    measured_unique_reach = len(covered_locations)
    overlap_count = max(0, declared_total_reach - measured_unique_reach)
    overlap_rate = (
        round((overlap_count / declared_total_reach) * 100.0, 1)
        if declared_total_reach > 0 else 0.0
    )

    declared_vs_measured = {
        "declared_total_reach": declared_total_reach,
        "measured_unique_reach": measured_unique_reach,
        "overlap_count": overlap_count,
        "overlap_percentage": overlap_rate,
        "important_total": len(important_locs),
        "important_covered": covered_important_count,
    }

    return OptimizationResult(
        timestamp=timestamp,
        config=config,
        graph=graph,
        mst_result=mst_result,
        knapsack_result=knapsack_result,
        dijkstra_result=dijkstra_result,
        covered_locations=covered_locations,
        uncovered_locations=uncovered_locations,
        coverage_percentage=coverage_pct,
        important_coverage_percentage=important_coverage_pct,
        avg_access_distance_covered=avg_dist_covered,
        avg_access_distance_all_reachable=avg_dist_reachable,
        max_access_distance=max_dist,
        efficiency_score=efficiency_score,
        declared_vs_measured_coverage=declared_vs_measured
    )

