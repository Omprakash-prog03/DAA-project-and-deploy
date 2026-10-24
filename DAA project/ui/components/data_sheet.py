from nicegui import ui
from typing import List, Dict, Any, Optional
from models.graph import Graph
from models.results import DijkstraResult
from models.config import Config
from ui.components.glass_card import glass_card

def render_bottom_data_sheet(
    graph: Graph,
    dijkstra_res: DijkstraResult,
    config: Config,
    avg_access_dist: float,
    on_row_focus: Optional[Any] = None
):
    """
    Bottom data sheet matching 'Schedule Offset' table from screenshot:
    - Large average access distance header: "+/- 3.8 km"
    - Table: Location | Nearest Station | Distance (with tick strip) | Status
    """
    with glass_card(extra_classes="w-full mt-3", padding="p-4"):
        # Header strip
        with ui.row().classes("w-full items-center justify-between mb-3 border-b border-white/5 pb-2"):
            with ui.row().classes("items-baseline gap-2"):
                ui.label("Access Distance").classes("text-sm font-medium text-[#ECEDEF]")
                ui.label(f"± {avg_access_dist:.1f} km").classes("text-lg font-light text-white font-mono tabular-nums")
                ui.label("Average Network Access Distance").classes("text-[11px] text-[#8B8F97]")

            ui.label(f"Threshold: {config.coverage_threshold_km} km").classes(
                "text-xs px-2.5 py-1 rounded-full bg-white/5 text-[#8B8F97] font-mono"
            )

        # Scrollable table container
        with ui.column().classes("w-full max-h-[190px] overflow-y-auto pr-1"):
            # Table Header
            with ui.row().classes("w-full text-[11px] uppercase tracking-wider text-[#5A5E66] font-medium py-1 px-2 border-b border-white/5"):
                ui.label("Location").classes("w-1/4")
                ui.label("Nearest Station").classes("w-1/4")
                ui.label("Access Distance").classes("w-1/3")
                ui.label("Status").classes("flex-1 text-right")

            # Table Rows
            for loc_id, loc in graph.locations.items():
                dist = dijkstra_res.distances.get(loc_id, float('inf'))
                nearest = dijkstra_res.nearest_seed.get(loc_id, "None")
                
                # Determine status and color
                if dist == float('inf'):
                    status_text = "UNREACHABLE"
                    status_color = "#FF4D4F"
                    row_bg = "hover:bg-[#FF4D4F]/5"
                    dist_display = "∞"
                    pct_width = 100
                elif dist <= config.coverage_threshold_km + 1e-7:
                    status_text = "COVERED"
                    status_color = "#3DDC84"
                    row_bg = "hover:bg-white/5"
                    dist_display = f"{dist:.1f} km"
                    pct_width = min(100, int((dist / config.coverage_threshold_km) * 100))
                else:
                    status_text = "OVER LIMIT"
                    status_color = "#F59E42"
                    row_bg = "hover:bg-[#F59E42]/5"
                    dist_display = f"{dist:.1f} km"
                    pct_width = 100

                with ui.row().classes(f"w-full items-center py-2 px-2 text-xs border-b border-white/[0.03] transition-colors {row_bg}"):
                    # Location
                    with ui.row().classes("w-1/4 items-center gap-1.5"):
                        ui.html(f'<div style="width: 6px; height: 6px; border-radius: 50%; background: {status_color};"></div>')
                        ui.label(loc.name).classes("font-medium text-[#ECEDEF] truncate")
                    
                    # Nearest station
                    ui.label(nearest or "None").classes("w-1/4 font-mono text-[#8B8F97] truncate")
                    
                    # Distance with thin tick-strip visual
                    with ui.row().classes("w-1/3 items-center gap-2"):
                        ui.label(dist_display).classes("font-mono tabular-nums text-white min-w-[50px]")
                        with ui.element("div").classes("flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden"):
                            ui.element("div").classes("h-full rounded-full").style(
                                f"width: {pct_width}%; background: {status_color}; transition: width 0.3s ease;"
                            )

                    # Status chip
                    with ui.row().classes("flex-1 justify-end"):
                        ui.label(status_text).classes("text-[10px] font-bold px-2 py-0.5 rounded-full").style(
                            f"background: {status_color}18; color: {status_color}; border: 1px solid {status_color}33;"
                        )
