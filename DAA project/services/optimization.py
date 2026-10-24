import datetime
from typing import List, Dict
from models.graph import Graph
from models.station import Station, KnapsackItem
from models.config import Config
from models.results import OptimizationResult
from algorithms.mst import kruskal_mst
from algorithms.knapsack import knapsack_01_optimize
from services.coverage import compute_physical_coverage
from services.evaluation import synthesize_optimization

def run_full_pipeline(
    graph: Graph,
    candidate_stations: List[Station],
    config: Config
) -> OptimizationResult:
    """
    Orchestrates the complete 4-stage algorithmic pipeline:
      1. Kruskal's Algorithm -> Grid Power Backbone (MST)
      2. Knapsack Formulation -> Feeder Integration Cost & DP Selection
      3. Multi-Source Dijkstra -> Physical Access Routing & Coverage
      4. Synthesis Service -> Multi-Objective Evaluation & Metrics
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # STAGE 1: Kruskal MST Backbone
    mst_result = kruskal_mst(graph, feeder_cost_per_km=config.feeder_cost_per_km)

    # Build lookup of incident MST edges for each location
    incident_mst_lengths: Dict[str, List[float]] = {loc_id: [] for loc_id in graph.locations}
    for road in mst_result.accepted_edges:
        incident_mst_lengths[road.u].append(road.distance_km)
        incident_mst_lengths[road.v].append(road.distance_km)

    # STAGE 2: 0/1 Knapsack Formulation with MST-Coupled Feeder Costs
    knapsack_items: List[KnapsackItem] = []
    for station in candidate_stations:
        incident = incident_mst_lengths.get(station.location_id, [])
        feeder_km = min(incident) if incident else 0.0
        feeder_cost = int(round(feeder_km * config.feeder_cost_per_km))
        net_weight = station.installation_cost + feeder_cost

        # Calculate integer benefit score
        raw_value = (
            config.coverage_weight * station.expected_coverage
            + config.capacity_weight * station.capacity_kw
            + config.priority_bonus_multiplier * station.priority
            + config.demand_weight * station.demand_score
        )
        benefit_value = max(1, int(round(raw_value)))

        knapsack_items.append(KnapsackItem(
            station=station,
            weight=net_weight,
            value=benefit_value,
            feeder_km=feeder_km,
            feeder_cost=feeder_cost
        ))

    # Apply backbone cost budget deduction toggle
    if config.include_backbone_in_budget:
        effective_knapsack_budget = max(0, config.total_budget - mst_result.backbone_cost)
    else:
        effective_knapsack_budget = config.total_budget

    knapsack_result = knapsack_01_optimize(
        items=knapsack_items,
        budget=effective_knapsack_budget,
        max_cells=config.max_dp_cells
    )

    # STAGE 3: Multi-Source Dijkstra for Physical Coverage
    selected_stations = [it.station for it in knapsack_result.selected_items]
    dijkstra_result, covered, uncovered = compute_physical_coverage(
        graph=graph,
        selected_stations=selected_stations,
        threshold_km=config.coverage_threshold_km
    )

    # STAGE 4: Synthesis & Metric Evaluation
    optimization_result = synthesize_optimization(
        timestamp=timestamp,
        config=config,
        graph=graph,
        mst_result=mst_result,
        knapsack_result=knapsack_result,
        dijkstra_result=dijkstra_result,
        covered_locations=covered,
        uncovered_locations=uncovered,
        all_stations=candidate_stations
    )

    return optimization_result

