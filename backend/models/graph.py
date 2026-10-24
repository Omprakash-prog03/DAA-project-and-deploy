from pydantic import BaseModel, Field
from typing import Dict, List, Tuple

class GraphNode(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float

class GraphEdge(BaseModel):
    u: str
    v: str
    road_distance_km: float = Field(..., gt=0.0)
    travel_time_min: float = 0.0
    is_real_road: bool = True

class WeightedGraph(BaseModel):
    """
    Undirected road-network graph.
    Nodes = Real EV stations or user points
    Edges = Real road distances obtained from routing API
    """
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)
    adjacency: Dict[str, List[Tuple[str, float]]] = Field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        if edge.u not in self.adjacency:
            self.adjacency[edge.u] = []
        if edge.v not in self.adjacency:
            self.adjacency[edge.v] = []
        self.adjacency[edge.u].append((edge.v, edge.road_distance_km))
        self.adjacency[edge.v].append((edge.u, edge.road_distance_km))

