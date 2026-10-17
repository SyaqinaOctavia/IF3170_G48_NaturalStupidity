from dataclasses import dataclass, field
from typing import List, Dict, Any
from utils import TruckState

@dataclass
class SearchResult:
    initial_state: TruckState
    final_state: TruckState
    obj_history: List[int]
    duration: float
    metrics: Dict[str, Any] = field(default_factory=dict)