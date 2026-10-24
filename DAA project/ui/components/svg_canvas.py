from typing import Dict, List, Set, Tuple, Optional
from models.graph import Graph
from models.location import Location
from models.station import Station

def generate_network_svg(
    graph: Graph,
    selected_stations: List[Station],
    mst_edges: Optional[List[str]] = None,
    rejected_edges: Optional[List[str]] = None,
    active_edge: Optional[str] = None,
    highlight_path_nodes: Optional[List[str]] = None,
    coverage_threshold_km: float = 5.0,
    covered_locations: Optional[List[str]] = None,
    selected_node_id: Optional[str] = None,
    show_labels: bool = True,
    show_weights: bool = True,
    view_width: int = 940,
    view_height: int = 580,
    zoom_scale: float = 1.0,
    pan_x: float = 0.0,
    pan_y: float = 0.0,
) -> str:
    """
    Renders the complete interactive dark SVG network canvas strictly matching
    the Traffic Management reference screenshot styling.
    """
    mst_set = set(mst_edges) if mst_edges else set()
    rejected_set = set(rejected_edges) if rejected_edges else set()
    covered_set = set(covered_locations) if covered_locations else set()
    selected_station_locs = {s.location_id for s in selected_stations}
    
    # Path edge lookup for glowing shortest path
    path_edges: Set[Tuple[str, str]] = set()
    if highlight_path_nodes and len(highlight_path_nodes) > 1:
        for i in range(len(highlight_path_nodes) - 1):
            u, v = highlight_path_nodes[i], highlight_path_nodes[i + 1]
            path_edges.add((u, v) if u <= v else (v, u))

    # Pixel radius for coverage circle (scaled relative to canvas dimensions)
    # E.g., 5.0 km corresponds to ~70px radius
    cov_px_radius = max(30, int(coverage_threshold_km * 14))

    elements = []

    # 1. Subtle topographic contour lines in background (~6% opacity)
    elements.append(f"""
    <g stroke="rgba(255,255,255,0.05)" fill="none" stroke-width="1.2">
        <path d="M 50,150 Q 250,50 480,180 T 900,120" />
        <path d="M 30,300 Q 300,180 550,320 T 920,260" />
        <path d="M 80,450 Q 350,380 620,480 T 900,420" />
        <ellipse cx="450" cy="280" rx="360" ry="220" stroke-dasharray="6,6" stroke="rgba(255,255,255,0.03)" />
    </g>
    """)

    # 2. Coverage Circles around SELECTED Stations (dashed rings with subtle radial glow)
    for loc_id in selected_station_locs:
        if loc_id in graph.locations:
            loc = graph.locations[loc_id]
            elements.append(f"""
            <circle cx="{loc.x}" cy="{loc.y}" r="{cov_px_radius}" 
                    fill="rgba(61, 220, 132, 0.03)" 
                    stroke="#3DDC84" 
                    stroke-width="1.2" 
                    stroke-dasharray="6,4" 
                    opacity="0.85"/>
            """)

    # 3. Roads (Edges)
    for road in graph.roads.values():
        u_loc = graph.locations.get(road.u)
        v_loc = graph.locations.get(road.v)
        if not u_loc or not v_loc:
            continue

        canon = road.canonical_endpoints
        is_mst = road.id in mst_set
        is_rej = road.id in rejected_set
        is_path = canon in path_edges
        is_active = (road.id == active_edge)

        # Style resolution
        if is_path:
            # Glowing white animated shortest path
            elements.append(f"""
            <line x1="{u_loc.x}" y1="{u_loc.y}" x2="{v_loc.x}" y2="{v_loc.y}" 
                  stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" 
                  filter="drop-shadow(0 0 8px rgba(255,255,255,0.8))" />
            """)
        elif is_active:
            # Active step in scrubber: golden pulse
            elements.append(f"""
            <line x1="{u_loc.x}" y1="{u_loc.y}" x2="{v_loc.x}" y2="{v_loc.y}" 
                  stroke="#F59E42" stroke-width="4" stroke-linecap="round" />
            """)
        elif is_mst:
            # Solid green MST feeder line
            elements.append(f"""
            <line x1="{u_loc.x}" y1="{u_loc.y}" x2="{v_loc.x}" y2="{v_loc.y}" 
                  stroke="#3DDC84" stroke-width="2.6" stroke-linecap="round" opacity="0.95" />
            """)
        elif is_rej:
            # Faint dashed red cycle road
            elements.append(f"""
            <line x1="{u_loc.x}" y1="{u_loc.y}" x2="{v_loc.x}" y2="{v_loc.y}" 
                  stroke="#FF4D4F" stroke-width="1.8" stroke-dasharray="4,4" opacity="0.6" />
            """)
        else:
            # Normal road: thin gray (30% opacity)
            elements.append(f"""
            <line x1="{u_loc.x}" y1="{u_loc.y}" x2="{v_loc.x}" y2="{v_loc.y}" 
                  stroke="rgba(255,255,255,0.22)" stroke-width="1.2" stroke-linecap="round" />
            """)

        # Distance labels
        if show_weights:
            mid_x = (u_loc.x + v_loc.x) / 2
            mid_y = (u_loc.y + v_loc.y) / 2
            elements.append(f"""
            <rect x="{mid_x - 13}" y="{mid_y - 8}" width="26" height="14" rx="4" fill="#0B0C0E" fill-opacity="0.85"/>
            <text x="{mid_x}" y="{mid_y + 3}" fill="#8B8F97" font-size="9" font-family="'Plus Jakarta Sans', monospace" 
                  text-anchor="middle" font-weight="500">{road.distance_km}k</text>
            """)

    # 4. Locations (Nodes)
    for loc in graph.locations.values():
        is_selected_station = loc.id in selected_station_locs
        is_covered = loc.id in covered_set
        is_focused = (loc.id == selected_node_id)
        
        # Click handler attribute triggering NiceGUI event
        node_click_attr = f'onclick="emitNodeClick(\'{loc.id}\')"'

        # Focused node golden glow ring
        if is_focused:
            elements.append(f"""
            <circle cx="{loc.x}" cy="{loc.y}" r="22" fill="none" stroke="#F59E42" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.8"/>
            """)

        # Important location outer ring
        if loc.is_important:
            ring_color = "#3DDC84" if is_covered else "#F59E42"
            elements.append(f"""
            <circle cx="{loc.x}" cy="{loc.y}" r="17" fill="none" stroke="{ring_color}" stroke-width="1.2" opacity="0.6"/>
            """)

        # Selected Station node styling: filled white marker with green dot
        if is_selected_station:
            elements.append(f"""
            <g class="cursor-pointer" {node_click_attr}>
                <circle cx="{loc.x}" cy="{loc.y}" r="12" fill="#FFFFFF" stroke="#3DDC84" stroke-width="2.5" />
                <circle cx="{loc.x}" cy="{loc.y}" r="4" fill="#3DDC84" />
            </g>
            """)
        else:
            # Standard location node: 14px circle (dark gray fill with white/colored ring)
            node_fill = "#14161A"
            node_stroke = "#3DDC84" if is_covered else "rgba(255,255,255,0.4)"
            elements.append(f"""
            <g class="cursor-pointer" {node_click_attr}>
                <circle cx="{loc.x}" cy="{loc.y}" r="8" fill="{node_fill}" stroke="{node_stroke}" stroke-width="1.8" />
            </g>
            """)

        # Node Text Label
        if show_labels:
            label_y = loc.y + 22
            elements.append(f"""
            <text x="{loc.x}" y="{label_y}" fill="#ECEDEF" font-size="11" font-weight="500" 
                  font-family="'Plus Jakarta Sans', sans-serif" text-anchor="middle" letter-spacing="-0.02em"
                  class="select-none pointer-events-none">{loc.name}</text>
            """)

    # Assemble SVG Viewport with Pan and Zoom transform
    inner_svg = "\n".join(elements)
    
    transform_attr = f'transform="translate({pan_x}, {pan_y}) scale({zoom_scale})"'

    full_svg = f"""
    <svg id="network-canvas-svg" width="100%" height="100%" viewBox="0 0 {view_width} {view_height}" 
         style="background: #0A0B0D; border-radius: 24px; user-select: none;" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <g id="viewport-group" {transform_attr}>
            {inner_svg}
        </g>
    </svg>
    """
    return full_svg
