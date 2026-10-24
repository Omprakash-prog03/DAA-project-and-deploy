import pytest
from models.config import Config
from models.graph import Graph
from models.location import Location
from models.road import Road
from models.station import Station
from data.demo_dataset import (
    get_demo_graph,
    get_demo_candidates,
    get_demo_config,
)
from services.optimization import run_full_pipeline
from services.sweep import run_budget_sweep

def test_full_pipeline_demo_dataset():
    graph = get_demo_graph()
    candidates = get_demo_candidates()
    config = get_demo_config()

    res = run_full_pipeline(graph, candidates, config)

    # 1. MST Verification
    assert len(res.mst_result.accepted_edges) == 12
    assert res.mst_result.components_count == 1
    assert res.mst_result.total_km > 0
    assert res.mst_result.backbone_cost > 0

    # 2. Knapsack Verification
    assert res.knapsack_result.total_weight <= config.total_budget
    assert len(res.knapsack_result.selected_items) > 0
    assert res.knapsack_result.remaining_budget == config.total_budget - res.knapsack_result.total_weight

    # 3. Dijkstra Coverage Verification
    assert len(res.covered_locations) + len(res.uncovered_locations) == len(graph.locations)
    assert 0.0 < res.coverage_percentage <= 100.0
    assert res.avg_access_distance_covered <= config.coverage_threshold_km + 1e-7
    assert res.max_access_distance >= res.avg_access_distance_covered

    # 4. Evaluation and Discrepancy Verification
    assert 0.0 <= res.efficiency_score <= 100.0
    assert "declared_total_reach" in res.declared_vs_measured_coverage
    assert "measured_unique_reach" in res.declared_vs_measured_coverage

def test_budget_monotonicity_property():
    """Higher budgets should yield monotonically non-decreasing total knapsack value."""
    graph = get_demo_graph()
    candidates = get_demo_candidates()

    budgets = [100000, 200000, 350000, 500000, 750000]
    previous_value = -1

    for b in budgets:
        cfg = Config(total_budget=b, coverage_threshold_km=5.0)
        res = run_full_pipeline(graph, candidates, cfg)
        current_value = res.knapsack_result.total_value
        assert current_value >= previous_value, f"Monotonicity violated at budget {b}: {current_value} < {previous_value}"
        assert res.knapsack_result.total_weight <= b
        previous_value = current_value

def test_threshold_monotonicity_property():
    """Larger coverage radius threshold should yield monotonically non-decreasing coverage percentage."""
    graph = get_demo_graph()
    candidates = get_demo_candidates()
    base_cfg = get_demo_config()

    thresholds = [2.0, 3.5, 5.0, 7.0, 10.0]
    previous_coverage = -1.0

    for t in thresholds:
        cfg = Config(
            total_budget=base_cfg.total_budget,
            coverage_threshold_km=t,
            feeder_cost_per_km=base_cfg.feeder_cost_per_km
        )
        res = run_full_pipeline(graph, candidates, cfg)
        assert res.coverage_percentage >= previous_coverage
        previous_coverage = res.coverage_percentage

def test_backbone_in_budget_toggle():
    """When backbone is included in budget, station budget is reduced by backbone cost."""
    graph = get_demo_graph()
    candidates = get_demo_candidates()

    cfg_without = Config(total_budget=600000, include_backbone_in_budget=False)
    res_without = run_full_pipeline(graph, candidates, cfg_without)

    cfg_with = Config(total_budget=600000, include_backbone_in_budget=True)
    res_with = run_full_pipeline(graph, candidates, cfg_with)

    # With backbone deducted, stations have less or equal money to spend
    assert res_with.knapsack_result.total_weight <= res_without.knapsack_result.total_weight
    assert res_with.knapsack_result.total_value <= res_without.knapsack_result.total_value

def test_disconnected_graph_pipeline_graceful_handling():
    """Ensures disconnected networks do not crash and unreachable nodes are marked uncovered."""
    g = Graph()
    g.add_location(Location("L1", "Main Hub", 0, 0))
    g.add_location(Location("L2", "Near Hub", 10, 0))
    g.add_location(Location("L_island", "Island", 100, 100)) # Disconnected
    g.add_road(Road("R1", "L1", "L2", 3.0))

    candidates = [
        Station("CS-1", "Main Station", "L1", installation_cost=50000, expected_coverage=2, capacity_kw=100, priority=2, demand_score=5.0)
    ]
    cfg = Config(total_budget=100000, coverage_threshold_km=5.0)

    res = run_full_pipeline(g, candidates, cfg)
    assert res.mst_result.components_count == 2
    assert "L_island" in res.uncovered_locations
    assert res.dijkstra_result.distances["L_island"] == float('inf')
    # Averages must be finite numbers without crash
    assert res.avg_access_distance_covered < float('inf')
    assert res.avg_access_distance_all_reachable < float('inf')

def test_budget_sweep_service():
    graph = get_demo_graph()
    candidates = get_demo_candidates()
    cfg = get_demo_config()

    sweep = run_budget_sweep(graph, candidates, cfg, steps=8)
    assert len(sweep) >= 7
    # Budgets should be strictly increasing
    budgets = [pt["budget"] for pt in sweep]
    assert budgets == sorted(budgets)

