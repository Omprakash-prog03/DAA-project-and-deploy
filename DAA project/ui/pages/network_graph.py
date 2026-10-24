from nicegui import ui
from ui.state import state
from ui.components.glass_card import glass_card, card_header
from ui.components.svg_canvas import generate_network_svg

def render_network_graph():
    res = state.result
    
    # Layer toggle states
    show_labels = True
    show_weights = True
    show_mst = True
    show_coverage_circles = True

    with ui.column().classes("w-[340px] p-5 gap-4 overflow-y-auto max-h-[calc(100vh-80px)]"):
        with glass_card(padding="p-4"):
            card_header("Graph Layer Controls", "Display Filters")
            
            lbl_chk = ui.checkbox("Location Labels", value=True).props("dark dense color=positive")
            wt_chk = ui.checkbox("Road Distances (km)", value=True).props("dark dense color=positive")
            mst_chk = ui.checkbox("Highlight MST Backbone", value=True).props("dark dense color=positive")
            cov_chk = ui.checkbox("Coverage Radius Rings", value=True).props("dark dense color=positive")

        # Node Inspector Card
        with glass_card(padding="p-4"):
            card_header("Topology Inspector", f"Focus: {state.selected_node_id}")
            loc = state.graph.locations.get(state.selected_node_id or "LOC-01")
            if loc:
                ui.label(loc.name).classes("text-lg font-medium text-white my-1")
                with ui.column().classes("gap-1 text-xs text-[#8B8F97]"):
                    ui.label(f"Location ID: {loc.id}")
                    ui.label(f"Important Landmark: {'Yes' if loc.is_important else 'Standard'}")
                    ui.label(f"Demand Factor: {loc.demand_factor}x")
                    
                    incident_roads = [
                        (nbr, wt, rid) for nbr, wt, rid in state.graph.adjacency.get(loc.id, [])
                    ]
                    ui.label(f"Degree: {len(incident_roads)} incident roads").classes("text-[#ECEDEF] font-medium mt-2")
                    for nbr, wt, rid in incident_roads:
                        nbr_name = state.graph.locations[nbr].name
                        ui.label(f"→ {nbr_name} ({wt} km)").classes("font-mono text-[11px] text-[#5A5E66]")

    # Large Graph Canvas
    with ui.column().classes("flex-1 p-5 max-h-[calc(100vh-80px)] overflow-y-auto"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Network Topology & Adjacency").classes("page-hero-title")
            ui.label(f"{len(state.graph.locations)} Vertices | {len(state.graph.roads)} Edges").classes(
                "text-xs px-3 py-1 rounded-full glass-pill text-[#8B8F97]"
            )

        canvas_box = ui.element("div").classes("w-full relative rounded-[24px] overflow-hidden border border-white/10")

        def update_canvas():
            canvas_box.clear()
            selected_stations = [it.station for it in res.knapsack_result.selected_items] if cov_chk.value else []
            mst_road_ids = [r.id for r in res.mst_result.accepted_edges] if mst_chk.value else []

            svg_str = generate_network_svg(
                graph=state.graph,
                selected_stations=selected_stations,
                mst_edges=mst_road_ids,
                coverage_threshold_km=state.config.coverage_threshold_km,
                covered_locations=res.covered_locations,
                selected_node_id=state.selected_node_id,
                show_labels=lbl_chk.value,
                show_weights=wt_chk.value,
                view_width=940,
                view_height=560
            )
            with canvas_box:
                ui.html(svg_str).classes("w-full block")

        lbl_chk.on_value_change(update_canvas)
        wt_chk.on_value_change(update_canvas)
        mst_chk.on_value_change(update_canvas)
        cov_chk.on_value_change(update_canvas)
        
        update_canvas()
