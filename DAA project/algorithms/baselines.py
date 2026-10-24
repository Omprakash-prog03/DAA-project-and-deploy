import heapq
from typing import Dict, List, Set, Tuple

from models.graph import Graph
from models.road import Road
from models.station import KnapsackItem

def prim_mst(graph: Graph) -> Tuple[float, List[Road]]:
    """
    Hand-written Prim's algorithm for Minimum Spanning Tree ground-truth cross-check.
    Applicable to connected components.
    
    Time Complexity: O((V + E) log V)
    Space Complexity: O(V + E)
    """
    if not graph.locations:
        return 0.0, []

    start_node = sorted(graph.locations.keys())[0]
    visited: Set[str] = {start_node}
    mst_edges: List[Road] = []
    total_km = 0.0

    # Min-heap of (weight, u, v, road_id)
    pq: List[Tuple[float, str, str, str]] = []
    
    for neighbor, weight, road_id in graph.adjacency.get(start_node, []):
        heapq.heappush(pq, (weight, start_node, neighbor, road_id))

    while pq and len(visited) < len(graph.locations):
        weight, u, v, road_id = heapq.heappop(pq)
        
        # If destination is already visited, this edge doesn't cross the cut
        if v in visited:
            continue

        visited.add(v)
        mst_edges.append(graph.roads[road_id])
        total_km += weight

        for next_neighbor, edge_weight, next_road_id in graph.adjacency.get(v, []):
            if next_neighbor not in visited:
                heapq.heappush(pq, (edge_weight, v, next_neighbor, next_road_id))

    return round(total_km, 2), mst_edges

def bellman_ford(graph: Graph, source: str) -> Dict[str, float]:
    """
    Hand-written Bellman-Ford algorithm for independent ground-truth verification of Dijkstra.
    Relaxes all edges |V| - 1 times.
    
    Time Complexity: O(V * E)
    Space Complexity: O(V)
    """
    distances: Dict[str, float] = {loc_id: float('inf') for loc_id in graph.locations}
    if source in distances:
        distances[source] = 0.0

    num_vertices = len(graph.locations)
    edge_list = []
    for road in graph.roads.values():
        edge_list.append((road.u, road.v, road.distance_km))
        edge_list.append((road.v, road.u, road.distance_km))

    for _ in range(num_vertices - 1):
        updated = False
        for u, v, w in edge_list:
            if distances[u] != float('inf') and distances[u] + w < distances[v] - 1e-7:
                distances[v] = round(distances[u] + w, 6)
                updated = True
        if not updated:
            break

    return distances

def brute_force_knapsack(items: List[KnapsackItem], budget: int) -> Tuple[int, List[KnapsackItem]]:
    """
    Exhaustive brute-force power set search (2^n) for ground-truth verification of 0/1 Knapsack DP.
    Only feasible for small n (n <= 16).
    """
    best_value = 0
    best_subset: List[KnapsackItem] = []
    n = len(items)

    for mask in range(1 << n):
        cur_weight = 0
        cur_value = 0
        subset = []
        for i in range(n):
            if (mask >> i) & 1:
                cur_weight += items[i].weight
                cur_value += items[i].value
                subset.append(items[i])
        
        if cur_weight <= budget:
            # Deterministic tie-breaker: prefer strictly higher value, then fewer items
            if cur_value > best_value:
                best_value = cur_value
                best_subset = subset
            elif cur_value == best_value and best_subset and len(subset) < len(best_subset):
                best_subset = subset

    return best_value, best_subset

def greedy_knapsack(items: List[KnapsackItem], budget: int) -> Tuple[int, int, List[KnapsackItem]]:
    """
    Greedy heuristic sorting items by benefit-to-cost ratio (value / weight).
    Demonstrates in viva that greedy is suboptimal compared to 0/1 Knapsack DP.
    
    Returns: (total_value, total_weight, selected_items)
    """
    # Sort by ratio descending; tie-break by weight ascending, then item ID
    sorted_items = sorted(
        items,
        key=lambda it: (it.value / it.weight if it.weight > 0 else float('inf'), -it.weight, it.station.id),
        reverse=True
    )
    
    selected = []
    total_w = 0
    total_v = 0
    
    for it in sorted_items:
        if total_w + it.weight <= budget:
            selected.append(it)
            total_w += it.weight
            total_v += it.value

    return total_v, total_w, selected


