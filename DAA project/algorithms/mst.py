from typing import List, Tuple
from models.graph import Graph
from models.road import Road
from models.results import MSTResult, KruskalStepTrace
from algorithms.union_find import DisjointSet

def kruskal_mst(graph: Graph, feeder_cost_per_km: int = 25000) -> MSTResult:
    """
    Computes Kruskal's Minimum Spanning Tree (or Forest if disconnected).
    
    DAA Specification:
    - Sorts edges lexicographically by (weight, min_id, max_id, road_id).
    - Uses Disjoint Set with path compression and union by rank.
    - Yields deterministic output.
    - Emits step-by-step trace record for UI replay.
    - Handles disconnected graphs as a Minimum Spanning Forest.
    
    Time Complexity: O(E log E) = O(E log V)
    Space Complexity: O(V + E)
    """
    if not graph.locations:
        return MSTResult(
            accepted_edges=[],
            rejected_edges=[],
            total_km=0.0,
            backbone_cost=0,
            components_count=0,
            traces=[]
        )

    # 1. Initialize Union-Find over all locations
    dsu = DisjointSet(graph.locations.keys())
    
    # 2. Extract edge list: (weight, min_id, max_id, road_id)
    sorted_edges = graph.get_edge_list()

    accepted: List[Road] = []
    rejected: List[Tuple[Road, str]] = []
    traces: List[KruskalStepTrace] = []
    running_total_km = 0.0

    # 3. Process edges in increasing order of weight
    for weight, u, v, road_id in sorted_edges:
        road = graph.roads[road_id]
        comps_before = dsu.num_components
        
        # Test if endpoints belong to different components
        if dsu.union(u, v):
            running_total_km += weight
            running_total_km = round(running_total_km, 4)
            accepted.append(road)
            trace = KruskalStepTrace(
                step_num=len(traces) + 1,
                road_id=road_id,
                u=u,
                v=v,
                weight=weight,
                decision="ACCEPTED",
                components_after=dsu.num_components,
                running_total_km=round(running_total_km, 2),
                reason=f"Connects disjoint components ({comps_before} -> {dsu.num_components})"
            )
            traces.append(trace)
        else:
            reason = f"Cycle detected: endpoints {u} and {v} are already connected"
            rejected.append((road, reason))
            trace = KruskalStepTrace(
                step_num=len(traces) + 1,
                road_id=road_id,
                u=u,
                v=v,
                weight=weight,
                decision="REJECTED_CYCLE",
                components_after=dsu.num_components,
                running_total_km=round(running_total_km, 2),
                reason=reason
            )
            traces.append(trace)

    final_total_km = round(running_total_km, 2)
    backbone_cost = int(round(final_total_km * feeder_cost_per_km))

    return MSTResult(
        accepted_edges=accepted,
        rejected_edges=rejected,
        total_km=final_total_km,
        backbone_cost=backbone_cost,
        components_count=dsu.num_components,
        traces=traces
    )

