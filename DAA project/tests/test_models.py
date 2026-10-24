import pytest
from models.location import Location
from models.road import Road
from models.graph import Graph
from models.station import Station
from models.config import Config
from data.demo_dataset import (
    DATASET_LABEL,
    get_demo_locations,
    get_demo_roads,
    get_demo_candidates,
    get_demo_graph,
    get_demo_config,
)

def test_location_validation():
    # Valid
    loc = Location(id="L1", name="Alpha", x=100.0, y=100.0)
    assert loc.id == "L1"
    assert loc.is_important is True

    # Invalid empty ID
    with pytest.raises(ValueError):
        Location(id="", name="Beta", x=0, y=0)

    # Invalid non-positive demand
    with pytest.raises(ValueError):
        Location(id="L2", name="Gamma", x=0, y=0, demand_factor=0)

def test_road_validation():
    # Valid
    road = Road(id="R1", u="L1", v="L2", distance_km=5.5)
    assert road.canonical_endpoints == ("L1", "L2")

    # Canonical order regardless of direction
    road_rev = Road(id="R2", u="L2", v="L1", distance_km=5.5)
    assert road_rev.canonical_endpoints == ("L1", "L2")

    # Self-loop error
    with pytest.raises(ValueError, match="Self-loop"):
        Road(id="R3", u="L1", v="L1", distance_km=2.0)

    # Zero or negative distance error
    with pytest.raises(ValueError, match="strictly positive"):
        Road(id="R4", u="L1", v="L2", distance_km=0.0)
    with pytest.raises(ValueError, match="strictly positive"):
        Road(id="R5", u="L1", v="L2", distance_km=-1.5)

def test_graph_construction_and_duplicate_handling():
    g = Graph()
    loc1 = Location(id="L1", name="Alpha", x=0, y=0)
    loc2 = Location(id="L2", name="Beta", x=10, y=10)
    loc3 = Location(id="L3", name="Gamma", x=20, y=20)
    g.add_location(loc1)
    g.add_location(loc2)
    g.add_location(loc3)

    # Missing endpoint raises error
    with pytest.raises(ValueError, match="endpoint v='L99' does not exist"):
        g.add_road(Road(id="R_bad", u="L1", v="L99", distance_km=5.0))

    # Add initial road
    r1 = Road(id="R1", u="L1", v="L2", distance_km=10.0)
    g.add_road(r1)
    assert len(g.roads) == 1
    assert len(g.adjacency["L1"]) == 1

    # Add duplicate road with LONGER distance -> keeps shorter, emits warning
    r2 = Road(id="R2", u="L2", v="L1", distance_km=15.0)
    g.add_road(r2)
    assert len(g.roads) == 1
    assert "R1" in g.roads
    assert any("keeping existing shorter" in w for w in g.warnings)

    # Add duplicate road with SHORTER distance -> replaces with shorter, emits warning
    r3 = Road(id="R3", u="L1", v="L2", distance_km=7.5)
    g.add_road(r3)
    assert len(g.roads) == 1
    assert "R3" in g.roads
    assert g.roads["R3"].distance_km == 7.5
    assert any("replacing" in w for w in g.warnings)

    # Check connectivity: L3 is currently isolated
    assert not g.is_connected()
    assert len(g.get_components()) == 2

    # Connect L3
    g.add_road(Road(id="R4", u="L2", v="L3", distance_km=4.0))
    assert g.is_connected()
    assert len(g.get_components()) == 1

def test_graph_edge_list_deterministic_sort():
    g = Graph()
    for i in range(1, 4):
        g.add_location(Location(id=f"L{i}", name=f"Loc {i}", x=0, y=0))
    # Two edges with same weight: tie-break by endpoints
    g.add_road(Road(id="R1", u="L2", v="L3", distance_km=5.0))
    g.add_road(Road(id="R2", u="L1", v="L3", distance_km=5.0))
    g.add_road(Road(id="R3", u="L1", v="L2", distance_km=2.0))

    edges = g.get_edge_list()
    assert edges[0] == (2.0, "L1", "L2", "R3")
    assert edges[1] == (5.0, "L1", "L3", "R2")
    assert edges[2] == (5.0, "L2", "L3", "R1")

def test_station_and_config_validation():
    # Valid station
    s = Station(id="S1", name="Hub", location_id="L1", installation_cost=100000,
                expected_coverage=4, capacity_kw=150, priority=2, demand_score=8.0)
    assert s.priority == 2

    # Invalid cost
    with pytest.raises(ValueError):
        Station(id="S2", name="Hub2", location_id="L1", installation_cost=-500,
                expected_coverage=2, capacity_kw=100, priority=1, demand_score=5.0)

    # Invalid priority tier
    with pytest.raises(ValueError):
        Station(id="S3", name="Hub3", location_id="L1", installation_cost=50000,
                expected_coverage=2, capacity_kw=100, priority=4, demand_score=5.0)

    # Valid config
    cfg = Config(total_budget=500000, coverage_threshold_km=5.0)
    assert cfg.total_budget == 500000

    # Negative budget error
    with pytest.raises(ValueError):
        Config(total_budget=-1)

    # Zero threshold error
    with pytest.raises(ValueError):
        Config(coverage_threshold_km=0.0)

def test_demo_dataset_integrity():
    assert DATASET_LABEL == "Demo Road Network"
    locs = get_demo_locations()
    assert len(locs) == 13
    assert sum(1 for l in locs if l.is_important) >= 10

    roads = get_demo_roads()
    assert len(roads) >= 20

    candidates = get_demo_candidates()
    assert 10 <= len(candidates) <= 12

    graph = get_demo_graph()
    assert len(graph.locations) == 13
    assert len(graph.roads) == len(roads)
    assert graph.is_connected()
    assert len(graph.validate()) == 0

