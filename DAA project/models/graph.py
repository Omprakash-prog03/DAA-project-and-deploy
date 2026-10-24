from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from models.location import Location
from models.road import Road

@dataclass
class Graph:
    """
    Undirected weighted graph represented as an adjacency list.
    Storage:
      locations: dict[node_id -> Location]
      roads: dict[road_id -> Road]
      adjacency: dict[node_id -> list of (neighbor_id, distance_km, road_id)]
    """
    locations: Dict[str, Location] = field(default_factory=dict)
    roads: Dict[str, Road] = field(default_factory=dict)
    adjacency: Dict[str, List[Tuple[str, float, str]]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def add_location(self, loc: Location) -> None:
        if loc.id in self.locations:
            raise ValueError(f"Duplicate location ID '{loc.id}'.")
        self.locations[loc.id] = loc
        if loc.id not in self.adjacency:
            self.adjacency[loc.id] = []

    def add_road(self, road: Road, merge_duplicate: bool = True) -> Optional[Road]:
        """
        Adds a road to the graph. If an existing road connects the same two endpoints:
        - If merge_duplicate=True: keeps the shorter road and records a warning.
        - Otherwise raises ValueError.
        """
        if road.u not in self.locations:
            raise ValueError(f"Road '{road.id}' endpoint u='{road.u}' does not exist.")
        if road.v not in self.locations:
            raise ValueError(f"Road '{road.id}' endpoint v='{road.v}' does not exist.")
        if road.id in self.roads:
            raise ValueError(f"Duplicate road ID '{road.id}'.")

        # Check for existing road between the same pair of endpoints
        u_canon, v_canon = road.canonical_endpoints
        for existing_road in list(self.roads.values()):
            if existing_road.canonical_endpoints == (u_canon, v_canon):
                if not merge_duplicate:
                    raise ValueError(f"Duplicate road connecting '{u_canon}' and '{v_canon}'.")
                
                if road.distance_km < existing_road.distance_km:
                    # Replace with shorter road
                    warn = (f"Duplicate road detected between {u_canon} and {v_canon}: "
                            f"replacing {existing_road.id} ({existing_road.distance_km} km) "
                            f"with shorter {road.id} ({road.distance_km} km).")
                    self.warnings.append(warn)
                    self._remove_road_from_adjacency(existing_road)
                    del self.roads[existing_road.id]
                    break
                else:
                    warn = (f"Duplicate road detected between {u_canon} and {v_canon}: "
                            f"keeping existing shorter {existing_road.id} ({existing_road.distance_km} km), "
                            f"ignoring {road.id} ({road.distance_km} km).")
                    self.warnings.append(warn)
                    return existing_road

        self.roads[road.id] = road
        self.adjacency[road.u].append((road.v, road.distance_km, road.id))
        self.adjacency[road.v].append((road.u, road.distance_km, road.id))
        return road

    def _remove_road_from_adjacency(self, road: Road) -> None:
        self.adjacency[road.u] = [
            t for t in self.adjacency[road.u] if t[2] != road.id
        ]
        self.adjacency[road.v] = [
            t for t in self.adjacency[road.v] if t[2] != road.id
        ]

    def get_edge_list(self) -> List[Tuple[float, str, str, str]]:
        """
        Returns unique undirected edges sorted deterministically for Kruskal:
        (distance_km, min_node_id, max_node_id, road_id)
        """
        edges = []
        for road in self.roads.values():
            u, v = road.canonical_endpoints
            edges.append((road.distance_km, u, v, road.id))
        
        # Deterministic tie-breaking by weight, then min_id, then max_id, then road_id
        edges.sort(key=lambda e: (e[0], e[1], e[2], e[3]))
        return edges

    def get_components(self) -> List[Set[str]]:
        """Finds all connected components via BFS."""
        visited: Set[str] = set()
        components: List[Set[str]] = []

        for loc_id in self.locations:
            if loc_id not in visited:
                comp: Set[str] = set()
                queue = [loc_id]
                visited.add(loc_id)
                while queue:
                    curr = queue.pop(0)
                    comp.add(curr)
                    for neighbor, _, _ in self.adjacency.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)
        return components

    def is_connected(self) -> bool:
        if not self.locations:
            return True
        return len(self.get_components()) <= 1

    def validate(self) -> List[str]:
        """Validates network properties and returns a list of warnings."""
        issues = list(self.warnings)
        if not self.locations:
            issues.append("Graph has no locations.")
        if not self.is_connected():
            comps = self.get_components()
            issues.append(f"Road network is disconnected into {len(comps)} separate components.")
        return issues

