import json
from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from models.location import Location
from models.road import Road
from models.station import Station
from models.config import Config

def render_dataset_editor():
    with ui.column().classes("w-full p-6 max-h-[calc(100vh-80px)] overflow-y-auto gap-5"):
        # Header and Actions Bar
        with glass_card(padding="p-5", extra_classes="w-full"):
            with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Dataset & Network Architecture Editor").classes("page-hero-title")
                    ui.label("Configure topology, edge weights, candidate stations, and budget limits.").classes("text-xs text-[#8B8F97]")

                with ui.row().classes("items-center gap-2"):
                    # Load Demo Dataset Button
                    ui.button(
                        "Load Demo Dataset",
                        icon="refresh",
                        on_click=lambda: (state.load_demo(), ui.notify("Canonical Demo Road Network loaded!", type="positive", position="top-right"))
                    ).props("rounded unelevated").classes("bg-[#3DDC84] text-[#0B0C0E] font-bold text-xs px-4 py-2 hover:opacity-90")

                    # Export JSON
                    def export_json():
                        data = {
                            "locations": [{"id": l.id, "name": l.name, "x": l.x, "y": l.y, "is_important": l.is_important, "demand_factor": l.demand_factor} for l in state.graph.locations.values()],
                            "roads": [{"id": r.id, "u": r.u, "v": r.v, "distance_km": r.distance_km} for r in state.graph.roads.values()],
                            "candidates": [{"id": s.id, "name": s.name, "location_id": s.location_id, "installation_cost": s.installation_cost, "expected_coverage": s.expected_coverage, "capacity_kw": s.capacity_kw, "priority": s.priority, "demand_score": s.demand_score} for s in state.candidates],
                            "config": {
                                "total_budget": state.config.total_budget,
                                "coverage_threshold_km": state.config.coverage_threshold_km,
                                "feeder_cost_per_km": state.config.feeder_cost_per_km,
                                "include_backbone_in_budget": state.config.include_backbone_in_budget
                            }
                        }
                        ui.download(json.dumps(data, indent=2).encode('utf-8'), "ev_network_dataset.json")

                    ui.button("Export JSON", icon="download", on_click=export_json).props("rounded outline").classes("text-xs text-white border-white/20 hover:bg-white/5")

        # Global System Configuration Form
        with glass_card(padding="p-5", extra_classes="w-full"):
            card_header("Global Optimization Parameters", "Pipeline Constraints", badge_text="Config", badge_color="#3DDC84")
            
            with ui.row().classes("w-full items-center gap-4 flex-wrap mt-2"):
                # Total Budget
                with ui.column().classes("gap-1 flex-1 min-w-[200px]"):
                    ui.label("Municipal Budget (₹ INR)").classes("text-[11px] text-[#8B8F97]")
                    budget_inp = ui.number(
                        value=state.config.total_budget,
                        step=25000,
                        min=0
                    ).props("dense dark outlined").classes("w-full text-xs")

                # Coverage Threshold
                with ui.column().classes("gap-1 flex-1 min-w-[200px]"):
                    ui.label("Coverage Threshold (km)").classes("text-[11px] text-[#8B8F97]")
                    thresh_inp = ui.number(
                        value=state.config.coverage_threshold_km,
                        step=0.5,
                        min=0.5,
                        max=30.0
                    ).props("dense dark outlined").classes("w-full text-xs")

                # Feeder Line Cost per km
                with ui.column().classes("gap-1 flex-1 min-w-[200px]"):
                    ui.label("Feeder Line Cost (₹/km)").classes("text-[11px] text-[#8B8F97]")
                    feeder_inp = ui.number(
                        value=state.config.feeder_cost_per_km,
                        step=5000,
                        min=0
                    ).props("dense dark outlined").classes("w-full text-xs")

                # Include Backbone in Budget Toggle
                with ui.column().classes("gap-1 flex-1 min-w-[220px]"):
                    ui.label("Deduct Backbone from Budget?").classes("text-[11px] text-[#8B8F97]")
                    backbone_toggle = ui.select(
                        options={False: "OFF (Backbone reported separately)", True: "ON (Deduct MST cost from station budget)"},
                        value=state.config.include_backbone_in_budget
                    ).props("dense dark outlined options-dense").classes("w-full text-xs")

            def on_config_save():
                try:
                    state.config = Config(
                        total_budget=int(budget_inp.value),
                        coverage_threshold_km=float(thresh_inp.value),
                        feeder_cost_per_km=int(feeder_inp.value),
                        include_backbone_in_budget=bool(backbone_toggle.value),
                        coverage_weight=state.config.coverage_weight,
                        capacity_weight=state.config.capacity_weight,
                        priority_bonus_multiplier=state.config.priority_bonus_multiplier,
                        demand_weight=state.config.demand_weight
                    )
                    state.recalculate()
                    ui.notify("Configuration saved and re-optimized!", type="positive", position="top-right")
                except Exception as ex:
                    ui.notify(f"Config error: {ex}", type="negative", position="top-right")

            ui.button("Apply Parameters", icon="check", on_click=on_config_save).props("dense outline").classes(
                "text-xs text-[#3DDC84] border-[#3DDC84]/30 mt-3 hover:bg-[#3DDC84]/10"
            )

        # Validation Warnings
        warnings = state.graph.validate()
        if warnings:
            with glass_card(padding="p-4", extra_classes="w-full bg-[#F59E42]/5 border-[#F59E42]/20"):
                with ui.row().classes("items-center gap-2 mb-1"):
                    ui.html('<span style="color: #F59E42;">⚠️</span>')
                    ui.label("Graph Validation Warnings").classes("text-xs font-bold text-[#F59E42]")
                for w in warnings:
                    ui.label(f"• {w}").classes("text-xs text-[#ECEDEF]")

        # Locations & Roads Tables
        with ui.row().classes("w-full gap-5"):
            # Locations Table
            with glass_card(padding="p-4", extra_classes="flex-1"):
                card_header(f"Locations ({len(state.graph.locations)})", "Network Nodes")
                with ui.column().classes("w-full max-h-[300px] overflow-y-auto pr-1 gap-1 mt-2"):
                    for loc in state.graph.locations.values():
                        with ui.row().classes("w-full items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5 text-xs"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(loc.id).classes("font-mono font-bold text-[#3DDC84]")
                                ui.label(loc.name).classes("text-white")
                            ui.label(f"({loc.x:.0f}, {loc.y:.0f})").classes("font-mono text-[11px] text-[#5A5E66]")

            # Roads Table
            with glass_card(padding="p-4", extra_classes="flex-1"):
                card_header(f"Road Segments ({len(state.graph.roads)})", "Bidirectional Weighted Links")
                with ui.column().classes("w-full max-h-[300px] overflow-y-auto pr-1 gap-1 mt-2"):
                    for road in state.graph.roads.values():
                        u_name = state.graph.locations[road.u].name
                        v_name = state.graph.locations[road.v].name
                        with ui.row().classes("w-full items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5 text-xs"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(road.id).classes("font-mono text-[#8B8F97]")
                                ui.label(f"{u_name} ↔ {v_name}").classes("text-white")
                            ui.label(f"{road.distance_km:.1f} km").classes("font-mono text-[#3DDC84] font-medium")
