from typing import List, Tuple
from models.location import Location
from models.road import Road
from models.graph import Graph
from models.station import Station
from models.config import Config

DATASET_LABEL = "Demo Road Network"

def get_demo_locations() -> List[Location]:
    """
    13 canonical locations with coordinates tailored for SVG rendering.
    11 of them are marked important.
    """
    return [
        Location(id="LOC-01", name="City Center", x=450.0, y=280.0, is_important=True, demand_factor=1.5),
        Location(id="LOC-02", name="Airport", x=740.0, y=120.0, is_important=True, demand_factor=1.4),
        Location(id="LOC-03", name="University", x=180.0, y=140.0, is_important=True, demand_factor=1.1),
        Location(id="LOC-04", name="Railway Station", x=310.0, y=410.0, is_important=True, demand_factor=1.6),
        Location(id="LOC-05", name="Hospital", x=490.0, y=130.0, is_important=True, demand_factor=1.3),
        Location(id="LOC-06", name="Shopping Mall", x=680.0, y=430.0, is_important=True, demand_factor=1.2),
        Location(id="LOC-07", name="Industrial Area", x=820.0, y=280.0, is_important=False, demand_factor=0.9),
        Location(id="LOC-08", name="Residential Area", x=130.0, y=460.0, is_important=False, demand_factor=0.8),
        Location(id="LOC-09", name="Highway Junction", x=90.0, y=280.0, is_important=True, demand_factor=1.4),
        Location(id="LOC-10", name="Bus Terminal", x=480.0, y=480.0, is_important=True, demand_factor=1.3),
        Location(id="LOC-11", name="Tech Park", x=650.0, y=250.0, is_important=True, demand_factor=1.2),
        Location(id="LOC-12", name="Market", x=290.0, y=270.0, is_important=True, demand_factor=1.2),
        Location(id="LOC-13", name="Stadium", x=600.0, y=60.0, is_important=True, demand_factor=1.0),
    ]

def get_demo_roads() -> List[Road]:
    """
    21 bidirectional roads with plausible distances.
    Includes duplicate weights (e.g. 3.0 km, 4.2 km) and distinct cycles.
    """
    return [
        Road(id="ROAD-01", u="LOC-12", v="LOC-01", distance_km=2.4),  # Market - City Center
        Road(id="ROAD-02", u="LOC-01", v="LOC-05", distance_km=2.8),  # City Center - Hospital
        Road(id="ROAD-03", u="LOC-01", v="LOC-11", distance_km=3.0),  # City Center - Tech Park (Duplicate wt)
        Road(id="ROAD-04", u="LOC-09", v="LOC-12", distance_km=3.0),  # Highway - Market (Duplicate wt)
        Road(id="ROAD-05", u="LOC-12", v="LOC-04", distance_km=3.2),  # Market - Railway
        Road(id="ROAD-06", u="LOC-03", v="LOC-12", distance_km=3.5),  # University - Market
        Road(id="ROAD-07", u="LOC-03", v="LOC-05", distance_km=4.2),  # University - Hospital (Duplicate wt)
        Road(id="ROAD-08", u="LOC-01", v="LOC-04", distance_km=3.8),  # City Center - Railway
        Road(id="ROAD-09", u="LOC-04", v="LOC-10", distance_km=3.6),  # Railway - Bus Terminal
        Road(id="ROAD-10", u="LOC-01", v="LOC-10", distance_km=4.0),  # City Center - Bus Terminal
        Road(id="ROAD-11", u="LOC-11", v="LOC-02", distance_km=4.2),  # Tech Park - Airport (Duplicate wt)
        Road(id="ROAD-12", u="LOC-05", v="LOC-13", distance_km=3.1),  # Hospital - Stadium
        Road(id="ROAD-13", u="LOC-13", v="LOC-02", distance_km=3.4),  # Stadium - Airport
        Road(id="ROAD-14", u="LOC-11", v="LOC-07", distance_km=3.7),  # Tech Park - Industrial
        Road(id="ROAD-15", u="LOC-07", v="LOC-02", distance_km=4.5),  # Industrial - Airport
        Road(id="ROAD-16", u="LOC-11", v="LOC-06", distance_km=4.1),  # Tech Park - Mall
        Road(id="ROAD-17", u="LOC-10", v="LOC-06", distance_km=4.6),  # Bus Terminal - Mall
        Road(id="ROAD-18", u="LOC-09", v="LOC-03", distance_km=4.8),  # Highway - University
        Road(id="ROAD-19", u="LOC-09", v="LOC-08", distance_km=3.9),  # Highway - Residential
        Road(id="ROAD-20", u="LOC-08", v="LOC-04", distance_km=4.4),  # Residential - Railway
        Road(id="ROAD-21", u="LOC-06", v="LOC-07", distance_km=5.2),  # Mall - Industrial
    ]

def get_demo_candidates() -> List[Station]:
    """11 candidate EV stations across key hub locations."""
    return [
        Station(id="CS-01", name="Airport Express Hub", location_id="LOC-02",
                installation_cost=110000, expected_coverage=4, capacity_kw=150, priority=3, demand_score=8.5),
        Station(id="CS-02", name="City Center Superstation", location_id="LOC-01",
                installation_cost=140000, expected_coverage=5, capacity_kw=200, priority=3, demand_score=9.5),
        Station(id="CS-03", name="University EcoCharge", location_id="LOC-03",
                installation_cost=85000, expected_coverage=3, capacity_kw=100, priority=1, demand_score=6.2),
        Station(id="CS-04", name="Railway Depot Station", location_id="LOC-04",
                installation_cost=125000, expected_coverage=5, capacity_kw=180, priority=3, demand_score=9.0),
        Station(id="CS-05", name="Hospital CarePoint", location_id="LOC-05",
                installation_cost=95000, expected_coverage=3, capacity_kw=120, priority=2, demand_score=7.4),
        Station(id="CS-06", name="Shopping Mall FastHub", location_id="LOC-06",
                installation_cost=105000, expected_coverage=4, capacity_kw=150, priority=2, demand_score=8.0),
        Station(id="CS-07", name="Industrial Logistics Power", location_id="LOC-07",
                installation_cost=155000, expected_coverage=3, capacity_kw=250, priority=2, demand_score=6.8),
        Station(id="CS-08", name="Residential Community Box", location_id="LOC-08",
                installation_cost=70000, expected_coverage=2, capacity_kw=60, priority=1, demand_score=5.0),
        Station(id="CS-09", name="Highway Interchange Rapid", location_id="LOC-09",
                installation_cost=145000, expected_coverage=4, capacity_kw=200, priority=3, demand_score=8.7),
        Station(id="CS-10", name="Bus Terminal Transit Fleet", location_id="LOC-10",
                installation_cost=120000, expected_coverage=4, capacity_kw=160, priority=2, demand_score=8.3),
        Station(id="CS-11", name="Tech Park CleanPower", location_id="LOC-11",
                installation_cost=100000, expected_coverage=4, capacity_kw=140, priority=2, demand_score=7.9),
    ]

def get_demo_graph() -> Graph:
    """Builds and returns the canonical Graph instance."""
    graph = Graph()
    for loc in get_demo_locations():
        graph.add_location(loc)
    for road in get_demo_roads():
        graph.add_road(road)
    return graph

def get_demo_config() -> Config:
    return Config(
        total_budget=500000,
        coverage_threshold_km=5.0,
        feeder_cost_per_km=25000,
        include_backbone_in_budget=False,
    )

