import heapq
from typing import Dict, List, Set, Tuple, Optional
from models.graph import Graph
from models.results import DijkstraResult, DijkstraStepTrace, DijkstraRelaxationTrace

def dijkstra_search(
    graph: Graph,
    source: str,
    target: Optional[str] = None
) -> DijkstraResult:
    """
    Single-source Dijkstra's algorithm using a binary min-heap with lazy deletion.
    If target is provided, search terminates early once target is visited.
    
    Time Complexity: O((V + E) log V)
    Space Complexity: O(V + E)
    """
    return _dijkstra_core(graph, seeds=[source], target=target, source_type="SINGLE_SOURCE")

def dijkstra_multi_source(
    graph: Graph,
    seed_locations: List[str]
) -> DijkstraResult:
    """
    Multi-source Dijkstra's algorithm initialized with distance 0 at all seed locations.
    Simultaneously discovers shortest paths and the nearest seed station for every node.
    
    Time Complexity: O((V + E) log V)
    Space Complexity: O(V + E)
    """
    return _dijkstra_core(graph, seeds=seed_locations, target=None, source_type="MULTI_SOURCE")

def _dijkstra_core(
    graph: Graph,
    seeds: List[str],
    target: Optional[str],
    source_type: str
) -> DijkstraResult:
    distances: Dict[str, float] = {loc_id: float('inf') for loc_id in graph.locations}
    predecessors: Dict[str, Optional[str]] = {loc_id: None for loc_id in graph.locations}
    nearest_seed: Dict[str, Optional[str]] = {loc_id: None for loc_id in graph.locations}
    visited: Set[str] = set()
    traces: List[DijkstraStepTrace] = []

    # Priority queue contains tuples of (distance, node_id)
    # Node_id provides deterministic lexicographical tie-breaking
    pq: List[Tuple[float, str]] = []

    for seed in seeds:
        if seed in graph.locations:
            distances[seed] = 0.0
            nearest_seed[seed] = seed
            heapq.heappush(pq, (0.0, seed))

    step_counter = 0

    while pq:
        curr_dist, u = heapq.heappop(pq)

        # Skip stale heap entries (lazy deletion)
        if u in visited:
            continue

        visited.add(u)
        step_counter += 1

        relax_traces: List[DijkstraRelaxationTrace] = []

        # Inspect all adjacent road links
        for v, weight, road_id in graph.adjacency.get(u, []):
            if v in visited:
                continue

            new_dist = round(curr_dist + weight, 6)
            old_dist = distances[v]

            # Epsilon-tolerant floating comparison
            if new_dist < old_dist - 1e-7:
                distances[v] = new_dist
                predecessors[v] = u
                nearest_seed[v] = nearest_seed[u]
                heapq.heappush(pq, (new_dist, v))
                relax_traces.append(DijkstraRelaxationTrace(
                    neighbor_id=v,
                    old_dist=old_dist,
                    new_dist=new_dist,
                    updated=True
                ))
            else:
                relax_traces.append(DijkstraRelaxationTrace(
                    neighbor_id=v,
                    old_dist=old_dist,
                    new_dist=old_dist,
                    updated=False
                ))

        traces.append(DijkstraStepTrace(
            step_num=step_counter,
            popped_node=u,
            dist=curr_dist,
            relaxations=relax_traces,
            visited_nodes=set(visited)
        ))

        # Early termination if single target found
        if target is not None and u == target:
            break

    return DijkstraResult(
        source_type=source_type,
        seed_nodes=seeds,
        distances=distances,
        predecessors=predecessors,
        nearest_seed=nearest_seed,
        traces=traces
    )

def reconstruct_path(
    result: DijkstraResult,
    target: str,
    graph: Graph
) -> Tuple[List[str], List[float], float]:
    """
    Reconstructs the shortest path from predecessors map.
    Returns:
      (node_sequence, per_edge_km_list, total_km)
    Handles:
      - Source == Target: ([Target], [], 0.0)
      - Unreachable: ([], [], float('inf'))
    """
    if target not in result.distances:
        return [], [], float('inf')

    total_dist = result.distances[target]
    if total_dist == float('inf'):
        return [], [], float('inf')

    # If target itself was one of the seeds with distance 0
    if target in result.seed_nodes and total_dist == 0.0:
        return [target], [], 0.0

    path = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        if curr in result.seed_nodes:
            break
        curr = result.predecessors.get(curr)

    path.reverse()

    # If we couldn't trace back to a seed
    if not path or path[0] not in result.seed_nodes:
        return [], [], float('inf')

    # Calculate per-edge distances
    edge_distances = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        # Find weight from adjacency
        w = None
        for neighbor, weight, _ in graph.adjacency.get(u, []):
            if neighbor == v:
                w = weight
                break
        if w is None:
            # Fallback
            w = round(result.distances[v] - result.distances[u], 4)
        edge_distances.append(w)

    return path, edge_distances, round(total_dist, 2)

