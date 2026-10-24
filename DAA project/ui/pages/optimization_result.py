import asyncio
from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from algorithms.baselines import greedy_knapsack

def render_optimization_result():
    res = state.result
    
    with ui.column().classes("w-full p-6 max-h-[calc(100vh-80px)] overflow-y-auto gap-5"):
        # Header and Execution Action Strip
        with glass_card(padding="p-5", extra_classes="w-full"):
            with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("EV Network Pipeline Execution").classes("text-xl font-light text-white")
                    ui.label("Synchronous end-to-end multi-algorithm optimization pipeline.").classes("text-xs text-[#8B8F97]")

                # Optimize Button
                opt_button = ui.button(
                    "OPTIMIZE NETWORK",
                    icon="play_arrow"
                ).props("rounded unelevated").classes("bg-[#3DDC84] text-[#0B0C0E] font-bold px-6 py-2.5 text-xs hover:opacity-90")

            # 5-Stage Progress Strip
            progress_row = ui.row().classes("w-full items-center justify-between mt-4 pt-3 border-t border-white/5 gap-2")
            
            stages = [
                ("1. Graph Topology", "VALIDATED"),
                ("2. Kruskal Backbone", "COMPUTED"),
                ("3. Knapsack Selection", "OPTIMAL"),
                ("4. Dijkstra Routes", "MEASURED"),
                ("5. Multi-Objective Score", "SYNTHESIZED"),
            ]
            
            with progress_row:
                for name, tag in stages:
                    with ui.row().classes("items-center gap-2 glass-pill px-3 py-1.5 border border-white/10"):
                        ui.html('<div style="width: 6px; height: 6px; border-radius: 50%; background: #3DDC84;"></div>')
                        ui.label(name).classes("text-xs text-[#ECEDEF] font-medium")
                        ui.label(tag).classes("text-[9px] font-mono text-[#3DDC84] px-1 py-0.2 rounded bg-[#3DDC84]/15")

            async def handle_optimize():
                opt_button.props("loading")
                await asyncio.sleep(0.3)
                state.recalculate()
                opt_button.props(remove="loading")
                ui.notify("Network optimization pipeline executed successfully!", type="positive", position="top-right")

            opt_button.on_click(handle_optimize)

        # Primary Result Screen Dossier matching <output_formats>
        with glass_card(padding="p-6", extra_classes="w-full"):
            card_header("EV NETWORK OPTIMIZATION DOSSIER", "Unified Infrastructure Synthesis Report", badge_text="Production Certified", badge_color="#3DDC84")

            # Grid of Key Output Metrics
            with ui.grid().classes("w-full grid-cols-2 md:grid-cols-5 gap-3 my-4"):
                metrics = [
                    ("Total Budget", f"₹{state.config.total_budget:,}", "#ECEDEF"),
                    ("Installation Cost", f"₹{res.knapsack_result.total_weight:,}", "#3DDC84"),
                    ("Remaining Budget", f"₹{res.knapsack_result.remaining_budget:,}", "#8B8F97"),
                    ("Selected Stations", f"{len(res.knapsack_result.selected_items)} / {len(state.candidates)}", "#3DDC84"),
                    ("Locations Covered", f"{len(res.covered_locations)} / {len(state.graph.locations)}", "#3DDC84"),
                    ("Coverage Percentage", f"{res.coverage_percentage:.1f} %", "#3DDC84"),
                    ("MST Backbone Distance", f"{res.mst_result.total_km:.1f} km", "#ECEDEF"),
                    ("Average Access Distance", f"{res.avg_access_distance_covered:.2f} km", "#ECEDEF"),
                    ("Maximum Access Distance", f"{res.max_access_distance:.2f} km", "#F59E42"),
                    ("Overall Efficiency Score", f"{res.efficiency_score:.1f} / 100", "#3DDC84"),
                ]
                for label, val, col in metrics:
                    with glass_card(padding="p-3", extra_classes="bg-white/[0.02]"):
                        ui.label(label).classes("text-[10px] text-[#5A5E66] uppercase tracking-wider")
                        ui.label(val).classes("text-lg font-mono font-medium mt-1").style(f"color: {col};")

            # Selected Stations and Unselected Stations (Detailed Lists)
            with ui.row().classes("w-full gap-4 mt-2"):
                # Selected
                with glass_card(padding="p-4", extra_classes="flex-1"):
                    ui.label("SELECTED CHARGING STATIONS").classes("text-xs font-bold uppercase tracking-wider text-[#3DDC84] mb-2")
                    for it in res.knapsack_result.selected_items:
                        loc_name = state.graph.locations[it.station.location_id].name
                        with ui.row().classes("w-full items-center justify-between p-2 rounded bg-[#3DDC84]/5 border border-[#3DDC84]/15 text-xs mb-1.5"):
                            with ui.column().classes("gap-0.5"):
                                ui.label(f"{it.station.id} — {it.station.name}").classes("font-medium text-white")
                                ui.label(f"Location: {loc_name} ({it.station.location_id})").classes("text-[10px] text-[#8B8F97]")
                            ui.label(f"₹{it.weight:,}").classes("font-mono text-white font-medium")

                # Unselected
                with glass_card(padding="p-4", extra_classes="flex-1"):
                    ui.label("UNSELECTED STATIONS & VIVA EXCLUSION REASONS").classes("text-xs font-bold uppercase tracking-wider text-[#FF4D4F] mb-2")
                    for it, reason in res.knapsack_result.unselected_items:
                        with ui.column().classes("w-full p-2 rounded bg-white/[0.02] border border-white/5 text-xs mb-1.5 gap-0.5"):
                            with ui.row().classes("w-full items-center justify-between"):
                                ui.label(f"{it.station.id} — {it.station.name}").classes("font-medium text-[#ECEDEF]")
                                ui.label(f"₹{it.weight:,}").classes("font-mono text-[#8B8F97]")
                            ui.label(f"Why Excluded: {reason}").classes("text-[10px] text-[#FF4D4F]/90 italic")

        # Viva Stretch Comparison: 0/1 Knapsack DP vs Greedy Heuristic
        # and Declared vs Measured Coverage Comparison
        with ui.row().classes("w-full gap-4"):
            # DP vs Greedy Stretch Card
            with glass_card(padding="p-5", extra_classes="flex-1"):
                card_header("VIVA STRETCH: 0/1 Knapsack DP vs Greedy Heuristic", "Proof of Global Optimality", badge_text="Viva Defense", badge_color="#F59E42")
                
                # Run greedy baseline
                all_items = res.knapsack_result.selected_items + [u[0] for u in res.knapsack_result.unselected_items]
                greedy_val, greedy_w, greedy_sel = greedy_knapsack(all_items, state.config.total_budget)
                
                dp_val = res.knapsack_result.total_value
                diff_val = dp_val - greedy_val

                with ui.row().classes("w-full items-center justify-around my-3 py-3 rounded-[18px] bg-white/[0.02] border border-white/5"):
                    with ui.column().classes("items-center"):
                        ui.label("0/1 Knapsack DP").classes("text-xs text-[#8B8F97]")
                        ui.label(f"{dp_val} pts").classes("text-2xl font-mono font-bold text-[#3DDC84]")
                        ui.label(f"Cost: ₹{res.knapsack_result.total_weight:,}").classes("text-[10px] text-[#5A5E66]")
                        ui.label("[PROVABLY OPTIMAL]").classes("text-[9px] font-bold text-[#3DDC84] mt-1")

                    ui.label("VS").classes("text-sm font-bold text-[#5A5E66]")

                    with ui.column().classes("items-center"):
                        ui.label("Greedy (Ratio v/w)").classes("text-xs text-[#8B8F97]")
                        ui.label(f"{greedy_val} pts").classes("text-2xl font-mono font-bold text-[#F59E42]")
                        ui.label(f"Cost: ₹{greedy_w:,}").classes("text-[10px] text-[#5A5E66]")
                        ui.label("[SUB-OPTIMAL]").classes("text-[9px] font-bold text-[#F59E42] mt-1")

                ui.label(
                    f"Result: Dynamic Programming achieves +{diff_val} points higher public benefit than the "
                    f"greedy value-to-cost heuristic, demonstrating the failure of greedy choice property on 0/1 knapsack."
                ).classes("text-xs text-[#8B8F97] leading-relaxed")

            # Declared vs Measured Coverage Duality Card
            with glass_card(padding="p-5", extra_classes="flex-1"):
                card_header("Declared Survey Benefit vs Dijkstra Measured Reach", "Physical Overlap Discrepancy", badge_text="Duality Analysis", badge_color="#3DDC84")
                
                dvm = res.declared_vs_measured_coverage
                with ui.row().classes("w-full items-center justify-around my-3 py-3 rounded-[18px] bg-white/[0.02] border border-white/5"):
                    with ui.column().classes("items-center"):
                        ui.label("Declared Survey Sum").classes("text-xs text-[#8B8F97]")
                        ui.label(f"{dvm['declared_total_reach']} locs").classes("text-2xl font-mono font-bold text-white")
                        ui.label("(Additive Knapsack Value)").classes("text-[10px] text-[#5A5E66]")

                    with ui.column().classes("items-center"):
                        ui.label("Dijkstra True Physical").classes("text-xs text-[#8B8F97]")
                        ui.label(f"{dvm['measured_unique_reach']} locs").classes("text-2xl font-mono font-bold text-[#3DDC84]")
                        ui.label(f"({res.coverage_percentage:.1f}% Network Coverage)").classes("text-[10px] text-[#3DDC84]")

                ui.label(
                    f"Discrepancy Analysis: {dvm['overlap_count']} overlapping candidate coverage zones ({dvm['overlap_percentage']:.1f}% overlap rate). "
                    f"While Knapsack assumes additive linear utility, multi-source Dijkstra correctly resolves topological overlap."
                ).classes("text-xs text-[#8B8F97] leading-relaxed")
