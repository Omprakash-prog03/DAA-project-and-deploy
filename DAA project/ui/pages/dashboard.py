from nicegui import ui
from typing import Callable, Optional
from ui.state import state
from ui.components.metrics import (
    render_chip_row,
    render_status_cards,
    render_coverage_card,
    render_station_cards_grid,
)
from ui.components.svg_canvas import generate_network_svg
from ui.components.data_sheet import render_bottom_data_sheet
from services.sweep import run_budget_sweep

def render_dashboard(on_node_focus: Optional[Callable[[str], None]] = None):
    res = state.result
    
    # Left Insight Panel (~36% width, stacked glass cards)
    with ui.column().classes("w-[380px] lg:w-[440px] xl:w-[480px] p-5 gap-4 overflow-y-auto max-h-[calc(100vh-80px)] pr-2"):
        render_chip_row(state.graph, state.config, len(state.candidates))
        
        selected_count = len(res.knapsack_result.selected_items)
        not_selected_count = len(state.candidates) - selected_count
        render_status_cards(selected_count, not_selected_count)
        
        # Coverage vs Budget parametric sweep
        sweep_data = run_budget_sweep(state.graph, state.candidates, state.config, steps=10)
        render_coverage_card(res.coverage_percentage, sweep_data, state.config.total_budget)
        
        # 2-column station cards
        render_station_cards_grid(
            res.knapsack_result.selected_items,
            on_station_select=on_node_focus
        )

    # Right Graph Canvas (~64% width, full bleed, rounded top-left corner)
    with ui.column().classes("flex-1 p-5 max-h-[calc(100vh-80px)] overflow-y-auto"):
        # Header Overlay
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.column().classes("gap-0.5"):
                ui.label("EV Network Planning").classes("page-hero-title")
                with ui.row().classes("items-center gap-2 mt-1"):
                    ui.label("Map View: Metro Autonomous Road Grid").classes("text-xs text-[#8B8F97]")
                    ui.label("● Live Analysis").classes("text-[10px] text-[#3DDC84] px-2 py-0.5 rounded-full bg-[#3DDC84]/10")

            # Quick Action Button
            ui.button("Recalculate Plan", on_click=lambda: state.recalculate(), icon="autorenew").props(
                "dense rounded outline"
            ).classes("text-xs text-white border-white/20 hover:bg-white/5")

        # SVG Canvas Container
        selected_stations = [it.station for it in res.knapsack_result.selected_items]
        mst_road_ids = [r.id for r in res.mst_result.accepted_edges]

        svg_content = generate_network_svg(
            graph=state.graph,
            selected_stations=selected_stations,
            mst_edges=mst_road_ids,
            coverage_threshold_km=state.config.coverage_threshold_km,
            covered_locations=res.covered_locations,
            selected_node_id=state.selected_node_id,
            show_labels=True,
            show_weights=True,
            view_width=920,
            view_height=490
        )
        
        with ui.element("div").classes("w-full relative rounded-[24px] overflow-hidden border border-white/10"):
            ui.html(svg_content).classes("w-full block")
            
            # Canvas floating Legend Overlay
            with ui.row().classes("absolute bottom-3 right-3 glass-panel px-3 py-1.5 rounded-full items-center gap-3 text-[10px] text-[#8B8F97]"):
                with ui.row().classes("items-center gap-1"):
                    ui.html('<div style="width: 14px; height: 2.5px; background: #3DDC84; border-radius: 2px;"></div>')
                    ui.label("MST Feeder")
                with ui.row().classes("items-center gap-1"):
                    ui.html('<div style="width: 14px; height: 1.5px; background: rgba(255,255,255,0.3); border-radius: 2px;"></div>')
                    ui.label("Road")
                with ui.row().classes("items-center gap-1"):
                    ui.html('<div style="width: 8px; height: 8px; border-radius: 50%; background: #FFFFFF; border: 1.5px solid #3DDC84;"></div>')
                    ui.label("Selected Station")

        # Bottom Data Sheet
        render_bottom_data_sheet(
            graph=state.graph,
            dijkstra_res=res.dijkstra_result,
            config=state.config,
            avg_access_dist=res.avg_access_distance_covered
        )
