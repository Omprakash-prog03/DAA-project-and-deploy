from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.config import settings
from backend.models.station import CandidateStation
from backend.models.graph import GraphNode, GraphEdge, WeightedGraph
from backend.models.route import Coordinates
from backend.models.optimization import MSTResponse, DijkstraResponse, KnapsackResponse
from backend.services.routing_service import get_real_road_distance_matrix, get_real_route_geometry
from backend.algorithms.mst import run_kruskal_mst
from backend.algorithms.dijkstra import run_dijkstra
from backend.algorithms.knapsack import run_01_knapsack

router = APIRouter(prefix="/api", tags=["DAA Algorithms"])


class MSTApiRequest(BaseModel):
    stations: List[CandidateStation] = Field(
        ..., min_length=2, max_length=settings.MAX_STATIONS_PER_REQUEST
    )
    feeder_cost_per_km: int = Field(default=25000, ge=1, le=1_000_000)


class DijkstraApiRequest(BaseModel):
    stations: List[CandidateStation] = Field(
        ..., max_length=settings.MAX_STATIONS_PER_REQUEST
    )
    start_id: Optional[str] = Field(default=None, max_length=100)
    destination_id: Optional[str] = Field(default=None, max_length=100)
    start_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    start_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    start_name: Optional[str] = Field(default="Origin", max_length=200)
    end_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    end_lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    end_name: Optional[str] = Field(default="Destination", max_length=200)


class KnapsackApiRequest(BaseModel):
    candidates: List[CandidateStation] = Field(
        ..., min_length=1, max_length=settings.MAX_KNAPSACK_CANDIDATES
    )
    budget: int = Field(..., ge=0, le=settings.MAX_BUDGET)


@router.post("/mst", response_model=MSTResponse)
def execute_mst_endpoint(req: MSTApiRequest):
    """
    Executes our hand-written Kruskal's MST algorithm on a graph
    constructed from real road-network distances between candidate stations.
    """
    # 1. Obtain real road distance matrix from routing service
    coords = [Coordinates(lat=s.latitude, lon=s.longitude) for s in req.stations]
    matrix_resp = get_real_road_distance_matrix(coords)
    matrix = matrix_resp.distances_km

    # 2. Build graph nodes and road edges
    nodes = {
        s.id: GraphNode(id=s.id, name=s.name, latitude=s.latitude, longitude=s.longitude)
        for s in req.stations
    }
    edges: List[GraphEdge] = []

    n = len(req.stations)
    for i in range(n):
        for j in range(i + 1, n):
            dist_km = matrix[i][j]
            if dist_km <= 0 and matrix[j][i] > 0:
                dist_km = matrix[j][i]
            elif dist_km > 0 and matrix[j][i] > 0:
                dist_km = min(dist_km, matrix[j][i])

            if dist_km > 0:
                edges.append(GraphEdge(
                    u=req.stations[i].id,
                    v=req.stations[j].id,
                    road_distance_km=round(dist_km, 3)
                ))

    # 3. Execute our hand-written Kruskal's algorithm
    mst_result = run_kruskal_mst(nodes, edges, feeder_cost_per_km=req.feeder_cost_per_km)
    mst_result.algorithm_info["road_data_source"] = matrix_resp.data_source
    return mst_result


@router.post("/dijkstra", response_model=DijkstraResponse)
def execute_dijkstra_endpoint(req: DijkstraApiRequest):
    """
    Executes our hand-written Dijkstra's shortest-path algorithm.
    Graph edges are real road distances. Route geometry is obtained from OSM routing API.
    Supports selecting stations by ID OR specifying custom Origin/Destination coordinates.
    """
    all_stations = list(req.stations)
    start_id = req.start_id
    dest_id = req.destination_id

    # Handle custom Origin coordinates if provided
    if req.start_lat is not None and req.start_lon is not None:
        start_id = "CUSTOM-ORIGIN"
        all_stations.append(CandidateStation(
            id=start_id,
            name=req.start_name or "Custom Origin",
            latitude=req.start_lat,
            longitude=req.start_lon,
            installation_cost=100000,
            expected_value=50,
            is_user_cost=True
        ))

    # Handle custom Destination coordinates if provided
    if req.end_lat is not None and req.end_lon is not None:
        dest_id = "CUSTOM-DESTINATION"
        all_stations.append(CandidateStation(
            id=dest_id,
            name=req.end_name or "Custom Destination",
            latitude=req.end_lat,
            longitude=req.end_lon,
            installation_cost=100000,
            expected_value=50,
            is_user_cost=True
        ))

    if len(all_stations) < 2:
        raise HTTPException(status_code=400, detail="At least 2 points required to calculate shortest path.")
    if len(all_stations) > settings.MAX_STATIONS_PER_REQUEST:
        raise HTTPException(
            status_code=422,
            detail=f"Shortest-path supports at most {settings.MAX_STATIONS_PER_REQUEST} points.",
        )

    station_lookup = {s.id: s for s in all_stations}
    if not start_id or start_id not in station_lookup:
        raise HTTPException(status_code=400, detail=f"Start location '{start_id}' not specified or found.")
    if not dest_id or dest_id not in station_lookup:
        raise HTTPException(status_code=400, detail=f"Destination location '{dest_id}' not specified or found.")

    # 1. Build weighted graph from real road distances
    coords = [Coordinates(lat=s.latitude, lon=s.longitude) for s in all_stations]
    matrix_resp = get_real_road_distance_matrix(coords)
    matrix = matrix_resp.distances_km

    graph = WeightedGraph()
    for s in all_stations:
        graph.add_node(GraphNode(id=s.id, name=s.name, latitude=s.latitude, longitude=s.longitude))

    n = len(all_stations)
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i][j] > 0:
                graph.add_edge(GraphEdge(
                    u=all_stations[i].id,
                    v=all_stations[j].id,
                    road_distance_km=round(matrix[i][j], 3)
                ))

    # 2. Get real road geometry for visual map rendering
    start_st = station_lookup[start_id]
    dest_st = station_lookup[dest_id]
    route_geom_resp = get_real_route_geometry(
        start_lat=start_st.latitude,
        start_lon=start_st.longitude,
        end_lat=dest_st.latitude,
        end_lon=dest_st.longitude
    )

    # 3. Execute our hand-written Dijkstra algorithm on the graph
    dijkstra_result = run_dijkstra(
        graph=graph,
        start_id=start_id,
        destination_id=dest_id,
        route_geometry=route_geom_resp.geometry_geojson
    )
    dijkstra_result.algorithm_info["road_data_source"] = matrix_resp.data_source
    dijkstra_result.algorithm_info["geometry_source"] = route_geom_resp.data_source
    return dijkstra_result


@router.post("/knapsack", response_model=KnapsackResponse)
def execute_knapsack_endpoint(req: KnapsackApiRequest):
    """
    Executes our hand-written 0/1 Knapsack Dynamic Programming algorithm.
    Optimizes candidate station selection under the user's budget.
    """
    return run_01_knapsack(candidates=req.candidates, budget=req.budget)
