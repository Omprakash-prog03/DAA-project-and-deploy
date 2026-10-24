from typing import List, Callable, Optional
from models.graph import Graph
from models.station import Station
from models.config import Config
from models.results import OptimizationResult
from data.demo_dataset import get_demo_graph, get_demo_candidates, get_demo_config
from services.optimization import run_full_pipeline

class AppState:
    """Central reactive application state for EV Network Planning."""
    def __init__(self):
        self.graph: Graph = get_demo_graph()
        self.candidates: List[Station] = get_demo_candidates()
        self.config: Config = get_demo_config()
        self.result: OptimizationResult = run_full_pipeline(self.graph, self.candidates, self.config)
        self.listeners: List[Callable[[], None]] = []
        
        # Interactive page states
        self.selected_node_id: Optional[str] = "LOC-01"
        self.shortest_path_source: str = "LOC-01"
        self.shortest_path_target: str = "LOC-02"
        self.active_tab: str = "Dashboard"

    def subscribe(self, listener: Callable[[], None]) -> None:
        if listener not in self.listeners:
            self.listeners.append(listener)

    def notify(self) -> None:
        for listener in self.listeners:
            try:
                listener()
            except Exception:
                pass

    def recalculate(self) -> OptimizationResult:
        self.result = run_full_pipeline(self.graph, self.candidates, self.config)
        self.notify()
        return self.result

    def load_demo(self) -> None:
        self.graph = get_demo_graph()
        self.candidates = get_demo_candidates()
        self.config = get_demo_config()
        self.selected_node_id = "LOC-01"
        self.recalculate()

# Global singleton state
state = AppState()
