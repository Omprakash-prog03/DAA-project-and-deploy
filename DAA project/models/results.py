from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from models.road import Road
from models.station import KnapsackItem
from models.config import Config
from models.graph import Graph

@dataclass(frozen=True)
class KruskalStepTrace:
    step_num: int
    road_id: str
    u: str
    v: str
    weight: float
    decision: str  # "ACCEPTED" or "REJECTED_CYCLE"
    components_after: int
    running_total_km: float
    reason: str

@dataclass
class MSTResult:
    accepted_edges: List[Road]
    rejected_edges: List[Tuple[Road, str]]
    total_km: float
    backbone_cost: int
    components_count: int
    traces: List[KruskalStepTrace]

@dataclass(frozen=True)
class DijkstraRelaxationTrace:
    neighbor_id: str
    old_dist: float
    new_dist: float
    updated: bool

@dataclass
class DijkstraStepTrace:
    step_num: int
    popped_node: str
    dist: float
    relaxations: List[DijkstraRelaxationTrace]
    visited_nodes: Set[str]

@dataclass
class DijkstraResult:
    source_type: str  # "SINGLE_SOURCE" or "MULTI_SOURCE"
    seed_nodes: List[str]
    distances: Dict[str, float]
    predecessors: Dict[str, Optional[str]]
    nearest_seed: Dict[str, Optional[str]]
    traces: List[DijkstraStepTrace]

@dataclass(frozen=True)
class KnapsackCellTrace:
    item_index: int
    item_id: str
    capacity_w: int
    take_value: int
    skip_value: int
    decision: str  # "TAKE" or "SKIP"

@dataclass
class KnapsackResult:
    selected_items: List[KnapsackItem]
    unselected_items: List[Tuple[KnapsackItem, str]]
    total_weight: int
    total_value: int
    remaining_budget: int
    scale_factor: int
    scaled_budget: int
    dp_table: List[List[int]]
    traces: List[KnapsackCellTrace]

@dataclass
class OptimizationResult:
    timestamp: str
    config: Config
    graph: Graph
    mst_result: MSTResult
    knapsack_result: KnapsackResult
    dijkstra_result: DijkstraResult
    covered_locations: List[str]
    uncovered_locations: List[str]
    coverage_percentage: float
    important_coverage_percentage: float
    avg_access_distance_covered: float
    avg_access_distance_all_reachable: float
    max_access_distance: float
    efficiency_score: float
    declared_vs_measured_coverage: Dict[str, Dict[str, Any]]

