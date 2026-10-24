from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from ui.components.svg_canvas import generate_network_svg
from ui.components.scrubber import StepScrubber
from algorithms.dijkstra import dijkstra_search, reconstruct_path

def render_shortest_path():
    loc_options = {loc.id: f"{loc.name} ({loc.id})" for loc in state.graph.locations.values()}
    
    # Run Dijkstra
    src = state.shortest_path_source
    dst = state.shortest_path_target
    dijkstra_res = dijkstra_search(state.graph, source=src, target=dst)
    path_nodes, edge_kms, total_dist = reconstruct_path(dijkstra_res, dst, state.graph)
    
    total_steps = max(1, len(dijkstra_res.traces))
    current_trace_step = [total_steps]

    with ui.column().classes("w-[380px] p-5 gap-4 overflow-y-auto max-h-[calc(100vh-80px)]"):
        # Source & Destination Selectors
        with glass_card(padding="p-4"):
            card_header("Route Query", "Dijkstra Shortest Path")
            
            with ui.column().classes("w-full gap-2 mt-2"):
                ui.label("Origin Node").classes("text-[11px] text-[#8B8F97]")
                src_select = ui.select(
                    options=loc_options,
                    value=src
                ).props("dense dark outlined options-dense").classes("w-full text-xs")

                ui.label("Destination Node").classes("text-[11px] text-[#8B8F97]")
                dst_select = ui.select(
                    options=loc_options,
                    value=dst
                ).props("dense dark outlined options-dense").classes("w-full text-xs")

                def on_route_change(_):
                    state.shortest_path_source = src_select.value
                    state.shortest_path_target = dst_select.value
                    state.notify()

                src_select.on_value_change(on_route_change)
                dst_select.on_value_change(on_route_change)

        # Route Metrics Card
        with glass_card(padding="p-4"):
            card_header("Path Solution", f"{len(path_nodes)} Waypoints", badge_text="O((V+E)logV)", badge_color="#3DDC84")
            
            with ui.row().classes("items-baseline gap-2 my-2"):
                dist_str = f"{total_dist:.2f}" if total_dist < float('inf') else "∞"
                ui.label(dist_str).classes("text-3xl font-light text-white font-mono tabular-nums")
                ui.label("km").classes("text-sm text-[#8B8F97]")

            # Step-by-step segment list
            if total_dist < float('inf') and len(path_nodes) > 1:
                with ui.column().classes("w-full gap-1.5 mt-2"):
                    for i in range(len(path_nodes) - 1):
                        u_name = state.graph.locations[path_nodes[i]].name
                        v_name = state.graph.locations[path_nodes[i + 1]].name
                        seg_dist = edge_kms[i]
                        with ui.row().classes("w-full items-center justify-between text-xs py-1 px-2 rounded bg-white/[0.02] border border-white/5"):
                            ui.label(f"{i+1}. {u_name} → {v_name}").classes("text-[#ECEDEF]")
                            ui.label(f"{seg_dist:.1f} km").classes("font-mono text-[#3DDC84] font-medium")
            elif src == dst:
                ui.label("Origin equals destination (Distance: 0.0 km).").classes("text-xs text-[#8B8F97] italic")
            else:
                ui.label("Target unreachable from origin in current network.").classes("text-xs text-[#FF4D4F]")

        # Trace details card
        trace_info_card = glass_card(padding="p-4")

    # Right Canvas and Scrubber
    with ui.column().classes("flex-1 p-5 max-h-[calc(100vh-80px)] overflow-y-auto"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.column().classes("gap-0.5"):
                ui.label("Optimal Route Traversal").classes("page-hero-title")
                ui.label(f"Single-source binary heap edge relaxation: {src} → {dst}").classes("text-xs text-[#8B8F97]")

        canvas_container = ui.element("div").classes("w-full relative rounded-[24px] overflow-hidden border border-white/10")

        def update_view(step_idx: int):
            current_trace_step[0] = step_idx
            canvas_container.clear()
            
            # Determine highlighted path up to this step
            subpath = path_nodes if step_idx >= total_steps else path_nodes[:min(len(path_nodes), step_idx + 1)]

            # Generate SVG
            svg_content = generate_network_svg(
                graph=state.graph,
                selected_stations=[],
                highlight_path_nodes=subpath,
                coverage_threshold_km=state.config.coverage_threshold_km,
                selected_node_id=path_nodes[min(len(path_nodes)-1, step_idx-1)] if path_nodes else None,
                show_labels=True,
                show_weights=True,
                view_width=940,
                view_height=520
            )
            with canvas_container:
                ui.html(svg_content).classes("w-full block")

            # Update trace info card
            trace_info_card.clear()
            with trace_info_card:
                if dijkstra_res.traces and 1 <= step_idx <= len(dijkstra_res.traces):
                    tr = dijkstra_res.traces[step_idx - 1]
                    node_name = state.graph.locations.get(tr.popped_node, tr.popped_node)
                    card_header(f"Heap Pop #{tr.step_num}", f"Node: {tr.popped_node} ({tr.dist:.1f} km)")
                    ui.label(f"Popped: {node_name.name if hasattr(node_name, 'name') else node_name}").classes("text-xs text-white font-medium")
                    
                    with ui.column().classes("w-full gap-1 mt-2 text-[11px] text-[#8B8F97]"):
                        ui.label(f"Visited Frontier: {len(tr.visited_nodes)} nodes").classes("font-mono")
                        for rel in tr.relaxations:
                            status_txt = "RELAXED" if rel.updated else "SKIPPED"
                            color = "#3DDC84" if rel.updated else "#5A5E66"
                            ui.label(f"• Neighbor {rel.neighbor_id}: {rel.old_dist:.1f} → {rel.new_dist:.1f} [{status_txt}]").classes(
                                f"font-mono text-[10px]"
                            ).style(f"color: {color};")

        scrubber = StepScrubber(
            total_steps=total_steps,
            on_step_change=update_view,
            label_prefix="Pop"
        )
        
        with ui.row().classes("w-full mt-3"):
            scrubber.render()

        update_view(total_steps)
