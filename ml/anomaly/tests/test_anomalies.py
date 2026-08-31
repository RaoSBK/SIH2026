import json
import os
from graph.generate_anomaly_data import generate_mock_graph
from ml.anomaly.anomaly_rules import load_graph, run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

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

def test_pipeline():
    workspace_root = get_workspace_root()
    data_dir = os.path.join(workspace_root, "data")
    graph_path = os.path.join(data_dir, "mock_graph.json")
    
    # 1. Generate fresh data with seeded anomalies
    print("--- 1. Generating Mock Data ---")
    generate_mock_graph(data_dir)
    
    # Load the graph
    graph = load_graph(graph_path)
    
    all_alerts = []
    
    # 2. Run Stage 1 (Rules)
    print("\n--- 2. Running Stage 1: Rule Engine ---")
    rule_alerts = run_rule_engine(graph)
    print(f"Found {len(rule_alerts)} rule-based anomalies.")
    all_alerts.extend(rule_alerts)
    
    # 3. Run Stage 2 (ML - Isolation Forest)
    print("\n--- 3. Running Stage 2: ML Isolation Forest ---")
    ml_alerts = run_ml_engine(graph)
    print(f"Found {len(ml_alerts)} ML-based anomalies.")
    all_alerts.extend(ml_alerts)
    
    # 4. Output results
    output_path = os.path.join(data_dir, "anomaly_alerts.json")
    with open(output_path, "w") as f:
        json.dump(all_alerts, f, indent=2)
        
    print(f"\n--- Output ---")
    print(f"Successfully saved {len(all_alerts)} alerts to {output_path}.")
    print("\nSample Alerts:")
    print(json.dumps(all_alerts[:3], indent=2))

if __name__ == "__main__":
    test_pipeline()
