import json
import os
from typing import Dict, List, Any
from .models.scoring import score_graph_anomalies

def get_workspace_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current:
        if os.path.exists(os.path.join(current, "docker-compose.yml")) or os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return r"d:\SIH2026"

def load_graph(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def run_ml_engine(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Stage 2: ML-based anomaly scoring using modular features and Isolation Forest model.
    """
    return score_graph_anomalies(graph_data)

if __name__ == "__main__":
    workspace_root = get_workspace_root()
    graph_path = os.path.join(workspace_root, "data", "mock_graph.json")
    if os.path.exists(graph_path):
        graph = load_graph(graph_path)
        alerts = run_ml_engine(graph)
        print(json.dumps(alerts, indent=2))
