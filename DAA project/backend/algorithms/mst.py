from typing import Dict, List, Tuple
from backend.models.graph import GraphNode, GraphEdge
from backend.models.optimization import MSTEdge, MSTResponse
from backend.algorithms.union_find import DisjointSet

def run_kruskal_mst(
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    feeder_cost_per_km: int = 25000
) -> MSTResponse:
    """
    Hand-written Kruskal's Minimum Spanning Tree / Forest algorithm.
    Operates on the graph constructed from real road network distances.
    
    DAA Academic Specifications:
    - Input: Graph G=(V,E) where edge weights are real road distances (km).
    - Processing:
      1. Sort edges in non-decreasing order of road distance with deterministic tie-breaking.
      2. For each edge (u, v), check if Find(u) == Find(v) (cycle detection).
      3. If endpoints are in disjoint components, union them and accept the edge into MST.
      4. If already connected, reject as cycle-inducing.
    - Output: Accepted backbone edges, total km, infrastructure cost, component count.
    - Time Complexity: O(E log E) = O(E log V) (sorting edges dominates; DSU takes O(E * alpha(V))).
    - Space Complexity: O(V + E) for DSU structures and edge representation.
    """
    if not nodes:
        return MSTResponse(
            accepted_edges=[],
            rejected_count=0,
            total_backbone_km=0.0,
            backbone_cost=0,
            connected_stations_count=0,
            total_edges_considered=0,
            algorithm_info={
                "algorithm": "Kruskal's MST (Hand-written)",
                "time_complexity": "O(E log V)",
                "space_complexity": "O(V + E)",
                "status": "Empty graph"
            }
        )

    # 1. Initialize Union-Find
    dsu = DisjointSet(nodes.keys())

    # 2. Extract unique undirected edges and sort deterministically
    unique_edges = []
    seen = set()
    for edge in edges:
        canon = (edge.u, edge.v) if edge.u <= edge.v else (edge.v, edge.u)
        if canon not in seen:
            seen.add(canon)
            unique_edges.append(edge)

    # Deterministic sort: (distance_km, min_node_id, max_node_id)
    unique_edges.sort(key=lambda e: (e.road_distance_km, min(e.u, e.v), max(e.u, e.v)))

    accepted_edges: List[MSTEdge] = []
    rejected_count = 0
    total_km = 0.0

    # 3. Kruskal's Main Greedy Loop
    for edge in unique_edges:
        u_node = nodes[edge.u]
        v_node = nodes[edge.v]

        if dsu.union(edge.u, edge.v):
            total_km += edge.road_distance_km
            accepted_edges.append(MSTEdge(
                u=edge.u,
                v=edge.v,
                u_name=u_node.name,
                v_name=v_node.name,
                u_lat=u_node.latitude,
                u_lon=u_node.longitude,
                v_lat=v_node.latitude,
                v_lon=v_node.longitude,
                road_distance_km=round(edge.road_distance_km, 2)
            ))
        else:
            rejected_count += 1

    total_km = round(total_km, 2)
    backbone_cost = int(round(total_km * feeder_cost_per_km))

    return MSTResponse(
        accepted_edges=accepted_edges,
        rejected_count=rejected_count,
        total_backbone_km=total_km,
        backbone_cost=backbone_cost,
        connected_stations_count=len(nodes),
        total_edges_considered=len(unique_edges),
        algorithm_info={
            "algorithm": "Kruskal's Algorithm (Hand-written Python)",
            "data_structure": "Disjoint Set Union (Rank + Path Compression)",
            "time_complexity": "O(E log V)",
            "space_complexity": "O(V + E)",
            "components_formed": dsu.num_components,
            "spanning_forest": dsu.num_components > 1,
            "invariant": "Acyclic subgraph minimizing total power feeder length across cuts"
        }
    )

