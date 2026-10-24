import pytest
from nicegui import ui
from ui.state import state
from ui.components.svg_canvas import generate_network_svg
from ui.components.metrics import _generate_sparkline_svg
from services.sweep import run_budget_sweep

def test_svg_canvas_rendering():
    res = state.result
    selected_stations = [it.station for it in res.knapsack_result.selected_items]
    mst_edges = [r.id for r in res.mst_result.accepted_edges]

    svg = generate_network_svg(
        graph=state.graph,
        selected_stations=selected_stations,
        mst_edges=mst_edges,
        rejected_edges=["ROAD-10"],
        active_edge="ROAD-01",
        highlight_path_nodes=["LOC-01", "LOC-02"],
        coverage_threshold_km=state.config.coverage_threshold_km,
        covered_locations=res.covered_locations,
        selected_node_id="LOC-01"
    )

    assert "<svg" in svg
    assert "</svg>" in svg
    assert "LOC-01" in svg
    assert "#3DDC84" in svg

def test_sparkline_svg_generation():
    sweep = run_budget_sweep(state.graph, state.candidates, state.config, steps=5)
    spark_svg = _generate_sparkline_svg(sweep, state.config.total_budget)
    assert "<svg" in spark_svg
    assert "polyline" in spark_svg

def test_state_recalculate_and_load_demo():
    old_res = state.result
    assert old_res is not None
    
    # Recalculate
    new_res = state.recalculate()
    assert new_res.knapsack_result.total_weight <= state.config.total_budget
    
    # Load demo
    state.load_demo()
    assert len(state.graph.locations) == 13
    assert len(state.candidates) >= 10

