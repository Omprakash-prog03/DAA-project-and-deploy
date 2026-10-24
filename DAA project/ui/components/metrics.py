from nicegui import ui
from typing import List, Dict, Any, Callable, Optional
from models.graph import Graph
from models.config import Config
from models.station import KnapsackItem
from ui.components.glass_card import glass_card, card_header

def render_chip_row(graph: Graph, config: Config, candidates_count: int):
    """Renders the top chip row: 13 Locations, 20 Roads, 10 Candidates, Budget."""
    with ui.row().classes("w-full gap-2 items-center flex-wrap"):
        chips = [
            (f"{len(graph.locations)} Locations", "#8B8F97"),
            (f"{len(graph.roads)} Roads", "#8B8F97"),
            (f"{candidates_count} Candidates", "#8B8F97"),
            (f"Budget ₹{config.total_budget:,}", "#3DDC84"),
        ]
        for label, color in chips:
            ui.label(label).classes(
                "text-xs px-3 py-1.5 rounded-full font-medium tracking-tight glass-pill text-[#ECEDEF]"
            ).style("border: 1px solid rgba(255,255,255,0.08);")

def render_status_cards(selected_count: int, not_selected_count: int):
    """Status cards (like Online 12 / Offline 4 from screenshot)."""
    with ui.row().classes("w-full gap-3"):
        # Online / Selected card
        with glass_card(extra_classes="flex-1", padding="p-4"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.html('<div style="width: 8px; height: 8px; border-radius: 50%; background: #3DDC84;"></div>')
                    ui.label("Selected").classes("text-xs text-[#8B8F97]")
                ui.label(str(selected_count)).classes("text-2xl font-light tabular-nums text-white")

        # Offline / Not Selected card
        with glass_card(extra_classes="flex-1", padding="p-4"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-2"):
                    ui.html('<div style="width: 8px; height: 8px; border-radius: 50%; background: #FF4D4F;"></div>')
                    ui.label("Not Selected").classes("text-xs text-[#8B8F97]")
                ui.label(str(not_selected_count)).classes("text-2xl font-light tabular-nums text-[#FF4D4F]")

def render_coverage_card(coverage_pct: float, sweep_data: List[Dict[str, Any]], current_budget: int):
    """Big metric coverage card with parametric curve (like Operational Efficiency)."""
    with glass_card(extra_classes="w-full", padding="p-5", hover_effect=True):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Operational Coverage").classes("text-sm text-[#8B8F97] font-medium")
            ui.html('<span style="color: #5A5E66; font-size: 14px;">↗</span>')
        
        # Big metric 75.0 %
        with ui.row().classes("items-baseline gap-1 my-1"):
            ui.label(f"{coverage_pct:.1f}").classes("big-metric-num")
            ui.label("%").classes("big-metric-unit")
        
        with ui.row().classes("w-full items-center justify-between text-[11px] text-[#5A5E66] mb-2"):
            ui.label("Target: 70.0%").classes("font-mono")
            ui.label(f"Current: ₹{current_budget:,}").classes("font-mono")

        # Parametric Sparkline SVG (Dynamic Coverage vs Budget curve)
        if sweep_data:
            svg_sparkline = _generate_sparkline_svg(sweep_data, current_budget)
            ui.html(svg_sparkline).classes("w-full")

def _generate_sparkline_svg(sweep_data: List[Dict[str, Any]], current_budget: int) -> str:
    width, height = 340, 65
    pad_x, pad_y = 10, 8
    
    budgets = [d["budget"] for d in sweep_data]
    coverages = [d["coverage_pct"] for d in sweep_data]
    
    min_b, max_b = min(budgets), max(budgets)
    min_c, max_c = 0.0, 100.0
    
    def scale_x(b):
        if max_b == min_b: return width / 2
        return pad_x + (b - min_b) / (max_b - min_b) * (width - 2 * pad_x)
    
    def scale_y(c):
        return height - pad_y - (c - min_c) / (max_c - min_c) * (height - 2 * pad_y)

    points = [(scale_x(d["budget"]), scale_y(d["coverage_pct"])) for d in sweep_data]
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    
    # Area path
    area_str = f"M {points[0][0]:.1f},{height - pad_y} " + " ".join(f"L {x:.1f},{y:.1f}" for x, y in points) + f" L {points[-1][0]:.1f},{height - pad_y} Z"
    
    # Target line at 70%
    target_y = scale_y(70.0)
    
    # Current budget marker
    cur_x = scale_x(current_budget)
    cur_y = scale_y(next((d["coverage_pct"] for d in sweep_data if d["budget"] == current_budget), coverages[len(coverages)//2]))

    svg = f"""
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="overflow: visible;">
        <defs>
            <linearGradient id="coverageGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3DDC84" stop-opacity="0.35"/>
                <stop offset="100%" stop-color="#3DDC84" stop-opacity="0.0"/>
            </linearGradient>
        </defs>
        <!-- Target line -->
        <line x1="{pad_x}" y1="{target_y:.1f}" x2="{width - pad_x}" y2="{target_y:.1f}" stroke="rgba(255,255,255,0.15)" stroke-dasharray="3,3" stroke-width="1"/>
        <!-- Area fill -->
        <path d="{area_str}" fill="url(#coverageGrad)" />
        <!-- Curve line -->
        <polyline fill="none" stroke="#3DDC84" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="{pts_str}" />
        <!-- Current budget dot -->
        <circle cx="{cur_x:.1f}" cy="{cur_y:.1f}" r="4" fill="#3DDC84" stroke="#0B0C0E" stroke-width="2"/>
    </svg>
    """
    return svg

def render_station_cards_grid(
    selected_items: List[KnapsackItem],
    on_station_select: Optional[Callable[[str], None]] = None
):
    """Renders 2-column station cards matching Bus 6023 cards in screenshot."""
    card_header("Optimal Station Deployment", f"{len(selected_items)} Active Units", badge_text="DP Optimal", badge_color="#3DDC84")
    
    with ui.grid().classes("w-full grid-cols-2 gap-3"):
        for it in selected_items:
            st = it.station
            with glass_card(extra_classes="p-3.5", hover_effect=True):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(st.id).classes("text-xs font-bold text-white tracking-wide")
                    ui.label("Online").classes("text-[10px] text-[#3DDC84] px-1.5 py-0.5 rounded-full bg-[#3DDC84]/10")
                
                ui.label(st.name).classes("text-[13px] font-medium text-[#ECEDEF] truncate my-0.5")
                
                with ui.row().classes("w-full items-center justify-between text-[11px] text-[#8B8F97] my-1"):
                    ui.label(f"₹{it.weight:,}").classes("tabular-nums text-white font-medium")
                    ui.label(f"+{it.value} pts").classes("text-[#3DDC84] font-medium")

                # Hardware tags
                with ui.row().classes("gap-1 items-center my-1"):
                    ui.label(f"{st.capacity_kw} kW").classes("text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-[#8B8F97]")
                    ui.label(f"P{st.priority}").classes("text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-[#8B8F97]")
                    ui.label(f"Feeder {it.feeder_km}km").classes("text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-[#8B8F97]")

                # Bottom mini route sketch representation
                with ui.row().classes("w-full items-center justify-between pt-1 border-t border-white/5 mt-1"):
                    ui.label(f"Loc: {st.location_id}").classes("text-[10px] text-[#5A5E66]")
                    if on_station_select:
                        ui.button(
                            "Focus",
                            on_click=lambda s_id=st.location_id: on_station_select(s_id)
                        ).props("flat dense").classes("text-[10px] text-[#3DDC84] p-0 min-h-0")
