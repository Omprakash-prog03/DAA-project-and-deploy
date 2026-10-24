from typing import Dict, List, Set, Tuple
from models.graph import Graph
from models.station import Station
from models.results import DijkstraResult
from algorithms.dijkstra import dijkstra_multi_source

def compute_physical_coverage(
    graph: Graph,
    selected_stations: List[Station],
    threshold_km: float
) -> Tuple[DijkstraResult, List[str], List[str]]:
    """
    Computes true physical coverage using multi-source Dijkstra over the full road network.
    
    A location is COVERED iff its shortest path distance to the nearest selected station
    is <= threshold_km + 1e-7 (epsilon tolerance).
    
    Returns:
      (dijkstra_result, covered_location_ids, uncovered_location_ids)
    """
    if not selected_stations or not graph.locations:
        # If no stations selected, all locations are uncovered
        d_res = dijkstra_multi_source(graph, seed_locations=[])
        return d_res, [], list(graph.locations.keys())

    # Extract unique station host locations
    seed_locations = list({s.location_id for s in selected_stations if s.location_id in graph.locations})
    dijkstra_res = dijkstra_multi_source(graph, seed_locations)

    covered: List[str] = []
    uncovered: List[str] = []

    for loc_id in graph.locations:
        dist = dijkstra_res.distances.get(loc_id, float('inf'))
        if dist <= threshold_km + 1e-7:
            covered.append(loc_id)
        else:
            uncovered.append(loc_id)

    # Sort for deterministic output
    covered.sort()
    uncovered.sort()

    return dijkstra_res, covered, uncovered

