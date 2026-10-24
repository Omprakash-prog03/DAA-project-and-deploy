import pytest
import random
from models.location import Location
from models.road import Road
from models.graph import Graph
from algorithms.dijkstra import dijkstra_search, dijkstra_multi_source, reconstruct_path
from algorithms.baselines import bellman_ford
from data.demo_dataset import get_demo_graph

def test_dijkstra_normal_and_path_reconstruction():
    graph = get_demo_graph()
    # City Center (LOC-01) to Airport (LOC-02)
    res = dijkstra_search(graph, source="LOC-01", target="LOC-02")
    
    assert res.distances["LOC-01"] == 0.0
    assert res.distances["LOC-02"] < float('inf')
    
    path, edge_kms, total_dist = reconstruct_path(res, "LOC-02", graph)
    assert path[0] == "LOC-01"
    assert path[-1] == "LOC-02"
    assert len(edge_kms) == len(path) - 1
    assert pytest.approx(sum(edge_kms), 1e-4) == total_dist
    assert pytest.approx(total_dist, 1e-4) == res.distances["LOC-02"]

def test_dijkstra_source_equals_destination():
    graph = get_demo_graph()
    res = dijkstra_search(graph, source="LOC-01", target="LOC-01")
    path, edge_kms, total_dist = reconstruct_path(res, "LOC-01", graph)
    
    assert total_dist == 0.0
    assert path == ["LOC-01"]
    assert edge_kms == []

def test_dijkstra_unreachable_node():
    g = Graph()
    g.add_location(Location("L1", "Loc1", 0, 0))
    g.add_location(Location("L2", "Loc2", 10, 0))
    g.add_location(Location("L3_isolated", "Isolated", 50, 50))
    g.add_road(Road("R1", "L1", "L2", 5.0))

    res = dijkstra_search(g, source="L1")
    assert res.distances["L1"] == 0.0
    assert res.distances["L2"] == 5.0
    assert res.distances["L3_isolated"] == float('inf')

    path, edge_kms, total_dist = reconstruct_path(res, "L3_isolated", g)
    assert total_dist == float('inf')
    assert path == []
    assert edge_kms == []

def test_dijkstra_multi_source_nearest_seed():
    graph = get_demo_graph()
    # Seeds: City Center (LOC-01) and Airport (LOC-02)
    seeds = ["LOC-01", "LOC-02"]
    res = dijkstra_multi_source(graph, seeds)

    assert res.distances["LOC-01"] == 0.0
    assert res.nearest_seed["LOC-01"] == "LOC-01"

    assert res.distances["LOC-02"] == 0.0
    assert res.nearest_seed["LOC-02"] == "LOC-02"

    # All nodes should be assigned to whichever seed is closer
    for loc_id in graph.locations:
        nearest = res.nearest_seed[loc_id]
        assert nearest in seeds
        # Distance from nearest seed must match
        d_from_seed1 = dijkstra_search(graph, "LOC-01").distances[loc_id]
        d_from_seed2 = dijkstra_search(graph, "LOC-02").distances[loc_id]
        expected_min = min(d_from_seed1, d_from_seed2)
        assert pytest.approx(res.distances[loc_id], 1e-4) == expected_min

def test_dijkstra_vs_bellman_ford_cross_check_demo():
    graph = get_demo_graph()
    for src in ["LOC-01", "LOC-02", "LOC-09"]:
        dijkstra_res = dijkstra_search(graph, source=src)
        bf_distances = bellman_ford(graph, source=src)

        for loc_id in graph.locations:
            assert pytest.approx(dijkstra_res.distances[loc_id], 1e-4) == bf_distances[loc_id]

def test_dijkstra_vs_bellman_ford_random_graphs():
    """Ground truth cross-check on randomly generated graphs with positive weights."""
    rng = random.Random(1337)

    for run in range(5):
        num_nodes = rng.randint(5, 10)
        g = Graph()
        nodes = [f"N{i}" for i in range(num_nodes)]
        for nid in nodes:
            g.add_location(Location(nid, f"Node {nid}", 0, 0))

        road_id = 1
        for i in range(num_nodes):
            u = nodes[i]
            v = nodes[(i + 1) % num_nodes]
            wt = round(rng.uniform(1.0, 10.0), 1)
            g.add_road(Road(f"R{road_id}", u, v, wt))
            road_id += 1

        source = nodes[0]
        dijkstra_res = dijkstra_search(g, source=source)
        bf_distances = bellman_ford(g, source=source)

        for nid in nodes:
            assert pytest.approx(dijkstra_res.distances[nid], 1e-4) == bf_distances[nid]

