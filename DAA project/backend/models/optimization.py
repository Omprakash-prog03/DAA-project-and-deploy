from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional, Any
from backend.models.station import CandidateStation

class MSTEdge(BaseModel):
    u: str
    v: str
    u_name: str
    v_name: str
    u_lat: float
    u_lon: float
    v_lat: float
    v_lon: float
    road_distance_km: float

class MSTResponse(BaseModel):
    accepted_edges: List[MSTEdge]
    rejected_count: int
    total_backbone_km: float
    backbone_cost: int
    connected_stations_count: int
    total_edges_considered: int
    algorithm_info: Dict[str, Any]

class DijkstraResponse(BaseModel):
    start_id: str
    destination_id: str
    path_node_ids: List[str]
    path_node_names: List[str]
    total_distance_km: float
    estimated_time_min: float
    per_edge_km: List[float]
    road_geometry_geojson: Optional[List[List[float]]] = None
    algorithm_info: Dict[str, Any]

class KnapsackResponse(BaseModel):
    selected_stations: List[CandidateStation]
    rejected_stations: List[Dict[str, Any]]
    total_installation_cost: int
    total_value_benefit: int
    remaining_budget: int
    budget_utilization_pct: float
    algorithm_info: Dict[str, Any]

