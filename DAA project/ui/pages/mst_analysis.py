from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from ui.components.svg_canvas import generate_network_svg
from ui.components.scrubber import StepScrubber

def render_mst_analysis():
    mst_res = state.result.mst_result
    traces = mst_res.traces
    total_steps = max(1, len(traces))
    current_step = [total_steps]

    with ui.column().classes("w-[420px] p-5 gap-4 overflow-y-auto max-h-[calc(100vh-80px)]"):
        # MST Summary Card
        with glass_card(padding="p-4"):
            card_header("Kruskal's MST Backbone", f"{len(mst_res.accepted_edges)} Accepted Segments", badge_text="O(E log V)", badge_color="#3DDC84")
            
            with ui.row().classes("w-full items-baseline justify-between my-2"):
                with ui.row().classes("items-baseline gap-1"):
                    ui.label(f"{mst_res.total_km:.1f}").classes("text-3xl font-light text-white font-mono tabular-nums")
                    ui.label("km").classes("text-sm text-[#8B8F97]")

                with ui.column().classes("items-end"):
                    ui.label("Feeder Line Cost").classes("text-[10px] text-[#5A5E66] uppercase")
                    ui.label(f"₹{mst_res.backbone_cost:,}").classes("text-sm font-mono text-[#3DDC84] font-medium")

            ui.label(f"Network Partition: {mst_res.components_count} Spanning Component(s)").classes(
                "text-xs text-[#8B8F97] font-medium"
            )

        # Sorted Edge Decision Ledger
        with glass_card(padding="p-4"):
            card_header("Edge Evaluation Queue", f"{len(traces)} roads inspected")
            
            with ui.column().classes("w-full max-h-[380px] overflow-y-auto pr-1 gap-1.5 mt-2"):
                for tr in traces:
                    u_name = state.graph.locations[tr.u].name
                    v_name = state.graph.locations[tr.v].name
                    is_acc = (tr.decision == "ACCEPTED")
                    badge_color = "#3DDC84" if is_acc else "#FF4D4F"
                    badge_label = "ACCEPTED" if is_acc else "REJECTED (CYCLE)"

                    with ui.row().classes(
                        f"w-full items-center justify-between p-2 rounded text-xs border border-white/5 "
                        f"{'bg-[#3DDC84]/5' if is_acc else 'bg-[#FF4D4F]/5'}"
                    ):
                        with ui.column().classes("gap-0.5 flex-1"):
                            ui.label(f"#{tr.step_num} {u_name} — {v_name}").classes("font-medium text-[#ECEDEF]")
                            ui.label(f"{tr.weight} km • {tr.reason}").classes("text-[10px] text-[#8B8F97]")
                        
                        ui.label(badge_label).classes(
                            "text-[9px] font-bold px-1.5 py-0.5 rounded-full"
                        ).style(f"color: {badge_color}; background: {badge_color}18; border: 1px solid {badge_color}33;")

    # Right Canvas and Kruskal Scrubber
    with ui.column().classes("flex-1 p-5 max-h-[calc(100vh-80px)] overflow-y-auto"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.column().classes("gap-0.5"):
                ui.label("Infrastructure Power Feeder Backbone").classes("page-hero-title")
                ui.label("Kruskal cycle detection via Disjoint Set Union by rank & path compression").classes("text-xs text-[#8B8F97]")

        canvas_box = ui.element("div").classes("w-full relative rounded-[24px] overflow-hidden border border-white/10")

        def update_mst_view(step_idx: int):
            current_step[0] = step_idx
            canvas_box.clear()
            
            # Active traces up to step_idx
            active_traces = traces[:step_idx]
            accepted_ids = [t.road_id for t in active_traces if t.decision == "ACCEPTED"]
            rejected_ids = [t.road_id for t in active_traces if t.decision == "REJECTED_CYCLE"]
            active_edge_id = traces[step_idx - 1].road_id if 1 <= step_idx <= len(traces) else None

            svg_str = generate_network_svg(
                graph=state.graph,
                selected_stations=[],
                mst_edges=accepted_ids,
                rejected_edges=rejected_ids,
                active_edge=active_edge_id,
                coverage_threshold_km=state.config.coverage_threshold_km,
                show_labels=True,
                show_weights=True,
                view_width=940,
                view_height=520
            )
            with canvas_box:
                ui.html(svg_str).classes("w-full block")

        scrubber = StepScrubber(
            total_steps=total_steps,
            on_step_change=update_mst_view,
            label_prefix="Edge"
        )
        
        with ui.row().classes("w-full mt-3"):
            scrubber.render()

        update_mst_view(total_steps)
