import heapq
from typing import Dict, List, Tuple, Optional
from backend.models.graph import WeightedGraph
from backend.models.optimization import DijkstraResponse

def run_dijkstra(
    graph: WeightedGraph,
    start_id: str,
    destination_id: str,
    route_geometry: Optional[List[List[float]]] = None
) -> DijkstraResponse:
    """
    Hand-written Dijkstra's algorithm using binary min-heap with edge relaxation.
    Independently calculates shortest graph path across real road network edges.
    
    DAA Academic Specifications:
    - Input: Graph G=(V,E) where edge weights are real road distances (km).
    - Processing:
      1. Initialize distance to start as 0.0, all other nodes as inf.
      2. Binary min-heap stores (dist, node_id) tuples.
      3. Repeatedly pop the minimum distance node u (Greedy choice property).
      4. Relax all outgoing edges (u, v): if dist[u] + w(u, v) < dist[v], update dist[v] and predecessor.
      5. Reconstruct path by walking backwards from destination_id.
    - Output: Shortest path node sequence, total graph km, per-edge km breakdown.
    - Time Complexity: O((V + E) log V) using binary min-heap with lazy deletion.
    - Space Complexity: O(V + E) for priority queue, distance table, and predecessor tree.
    """
    if start_id not in graph.nodes or destination_id not in graph.nodes:
        raise ValueError("Start or Destination node does not exist in graph.")

    distances: Dict[str, float] = {nid: float('inf') for nid in graph.nodes}
    predecessors: Dict[str, Optional[str]] = {nid: None for nid in graph.nodes}
    visited = set()

    distances[start_id] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, start_id)]

    while pq:
        curr_dist, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        if u == destination_id:
            break

        for v, weight in graph.adjacency.get(u, []):
            if v in visited:
                continue

            new_dist = round(curr_dist + weight, 4)
            # Epsilon tolerance for floating-point relaxation
            if new_dist < distances[v] - 1e-7:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    # Path Reconstruction
    total_dist = distances[destination_id]
    if total_dist == float('inf'):
        return DijkstraResponse(
            start_id=start_id,
            destination_id=destination_id,
            path_node_ids=[],
            path_node_names=[],
            total_distance_km=float('inf'),
            estimated_time_min=0.0,
            per_edge_km=[],
            road_geometry_geojson=None,
            algorithm_info={
                "algorithm": "Dijkstra's Algorithm (Hand-written Python)",
                "status": "Unreachable",
                "time_complexity": "O((V + E) log V)",
                "space_complexity": "O(V + E)"
            }
        )

    # Reconstruct path from destination to start
    path_ids = []
    curr = destination_id
    while curr is not None:
        path_ids.append(curr)
        if curr == start_id:
            break
        curr = predecessors[curr]

    path_ids.reverse()

    # Calculate per-edge distances
    per_edge: List[float] = []
    for i in range(len(path_ids) - 1):
        u, v = path_ids[i], path_ids[i + 1]
        w = round(distances[v] - distances[u], 2)
        per_edge.append(w)

    path_names = [graph.nodes[nid].name for nid in path_ids]
    # Estimated time assuming city/highway mixed driving average ~45 km/h
    est_time = round((total_dist / 45.0) * 60.0, 1)

    return DijkstraResponse(
        start_id=start_id,
        destination_id=destination_id,
        path_node_ids=path_ids,
        path_node_names=path_names,
        total_distance_km=round(total_dist, 2),
        estimated_time_min=est_time,
        per_edge_km=per_edge,
        road_geometry_geojson=route_geometry,
        algorithm_info={
            "algorithm": "Dijkstra's Shortest Path (Hand-written Python)",
            "priority_queue": "Binary Min-Heap with Lazy Deletion",
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V + E)",
            "triangle_inequality": "Guaranteed minimal path distance",
            "separation_note": "Graph path computed purely by our Dijkstra; route_geometry is external OSM visual overlay"
        }
    )

