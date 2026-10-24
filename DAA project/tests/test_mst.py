import pytest
import random
from models.location import Location
from models.road import Road
from models.graph import Graph
from algorithms.mst import kruskal_mst
from algorithms.baselines import prim_mst
from data.demo_dataset import get_demo_graph

def test_kruskal_connected_demo_network():
    graph = get_demo_graph()
    result = kruskal_mst(graph, feeder_cost_per_km=25000)

    # In a connected graph of 13 vertices, a spanning tree has exactly 12 edges
    assert len(result.accepted_edges) == 12
    assert result.components_count == 1
    assert result.total_km > 0
    assert result.backbone_cost == int(round(result.total_km * 25000))

    # All 21 edges in demo graph should be processed (12 accepted, 9 rejected)
    assert len(result.traces) == 21
    assert len(result.rejected_edges) == 9

    # Verify every rejected edge was classified as REJECTED_CYCLE
    for _, reason in result.rejected_edges:
        assert "Cycle detected" in reason

def test_kruskal_duplicate_weights_deterministic():
    # Build diamond graph with two equal-weight paths
    # L1 -(3.0)- L2 -(3.0)- L4
    # L1 -(3.0)- L3 -(3.0)- L4
    g = Graph()
    g.add_location(Location("L1", "Loc1", 0, 0))
    g.add_location(Location("L2", "Loc2", 10, 0))
    g.add_location(Location("L3", "Loc3", 0, 10))
    g.add_location(Location("L4", "Loc4", 10, 10))

    # All edges have distance 3.0
    g.add_road(Road("R1", "L1", "L2", 3.0))
    g.add_road(Road("R2", "L2", "L4", 3.0))
    g.add_road(Road("R3", "L1", "L3", 3.0))
    g.add_road(Road("R4", "L3", "L4", 3.0))

    res1 = kruskal_mst(g)
    res2 = kruskal_mst(g)

    # Determinism: exact same accepted edges and total km
    assert res1.total_km == 9.0
    assert len(res1.accepted_edges) == 3
    assert len(res1.rejected_edges) == 1
    assert [e.id for e in res1.accepted_edges] == [e.id for e in res2.accepted_edges]

def test_kruskal_disconnected_graph_spanning_forest():
    # Graph with 2 disconnected components: {L1, L2} and {L3, L4, L5}
    g = Graph()
    for i in range(1, 6):
        g.add_location(Location(f"L{i}", f"Loc{i}", 0, 0))

    # Component 1
    g.add_road(Road("R1", "L1", "L2", 4.0))

    # Component 2 (triangle)
    g.add_road(Road("R2", "L3", "L4", 2.0))
    g.add_road(Road("R3", "L4", "L5", 3.0))
    g.add_road(Road("R4", "L3", "L5", 6.0)) # cycle

    res = kruskal_mst(g)
    assert res.components_count == 2
    # Total accepted edges in forest with V=5, C=2 is V - C = 3
    assert len(res.accepted_edges) == 3
    assert len(res.rejected_edges) == 1
    assert res.rejected_edges[0][0].id == "R4"
    assert res.total_km == 4.0 + 2.0 + 3.0

def test_kruskal_vs_prim_cross_check_demo():
    graph = get_demo_graph()
    kruskal_res = kruskal_mst(graph)
    prim_total, prim_edges = prim_mst(graph)

    # Prim and Kruskal MUST produce identical total MST weights
    assert pytest.approx(kruskal_res.total_km, 1e-4) == prim_total
    assert len(prim_edges) == len(kruskal_res.accepted_edges) == 12

def test_kruskal_vs_prim_random_graphs():
    """Ground truth cross-check on randomly generated connected graphs with seeded PRNG."""
    rng = random.Random(42)

    for run in range(5):
        num_nodes = rng.randint(6, 12)
        g = Graph()
        nodes = [f"N{i}" for i in range(num_nodes)]
        for nid in nodes:
            g.add_location(Location(nid, f"Name {nid}", 0, 0))

        # Ensure connectivity by creating a random backbone
        road_id = 1
        for i in range(1, num_nodes):
            prev = nodes[rng.randint(0, i - 1)]
            curr = nodes[i]
            wt = round(rng.uniform(1.0, 15.0), 1)
            g.add_road(Road(f"R{road_id}", prev, curr, wt))
            road_id += 1

        # Add additional random cycle-forming edges
        for _ in range(num_nodes):
            u, v = rng.sample(nodes, 2)
            wt = round(rng.uniform(1.0, 15.0), 1)
            try:
                g.add_road(Road(f"R{road_id}", u, v, wt), merge_duplicate=False)
                road_id += 1
            except ValueError:
                pass # skip duplicates

        kruskal_res = kruskal_mst(g)
        prim_total, prim_edges = prim_mst(g)

        assert pytest.approx(kruskal_res.total_km, 1e-4) == prim_total
        assert len(kruskal_res.accepted_edges) == num_nodes - 1

