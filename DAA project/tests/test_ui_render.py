import pytest
from ui.state import state
from ui.pages import (
    render_dashboard,
    render_network_graph,
    render_station_planning,
    render_shortest_path,
    render_mst_analysis,
    render_knapsack_analysis,
    render_optimization_result,
    render_dataset_editor,
    render_about_algorithms,
)
from nicegui import ui

def test_all_pages_render_without_exception():
    """Verifies that all 9 UI views construct their components and traces without error."""
    pages = [
        render_dashboard,
        render_network_graph,
        render_station_planning,
        render_shortest_path,
        render_mst_analysis,
        render_knapsack_analysis,
        render_optimization_result,
        render_dataset_editor,
        render_about_algorithms,
    ]

    for page_fn in pages:
        with ui.element('div'):
            page_fn()
