import json
import uuid
import os
import numpy as np
from collections import defaultdict
from sklearn.ensemble import IsolationForest

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

def extract_features(graph_data):
    """
    Extract behavioral features for each node to feed into Isolation Forest.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])
    
    # Features:
    # 1. Total transaction volume (outgoing)
    # 2. Total number of transactions (outgoing)
    # 3. Total call duration (outgoing)
    # 4. Out-degree (number of unique targets)
    
    features = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    unique_targets = defaultdict(set)
    evidence_map = defaultdict(list)
    
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        unique_targets[source].add(target)
        
        # Collect evidence (edges)
        evidence_map[source].append(edge["id"])
        
        if edge["type"] == "TRANSACTION":
            features[source][0] += edge["amount"]
            features[source][1] += 1
        elif edge["type"] == "CALL":
            features[source][2] += edge["duration"]
            
    for source in features:
        features[source][3] = float(len(unique_targets[source]))
        
    # Build X matrix
    entity_ids = list(features.keys())
    X = np.array([features[eid] for eid in entity_ids])
    
    return entity_ids, X, evidence_map

def run_ml_engine(graph_data):
    """
    Stage 2: ML-based anomaly scoring using Isolation Forest.
    """
    entity_ids, X, evidence_map = extract_features(graph_data)
    
    if len(entity_ids) == 0:
        return []
        
    # Fit Isolation Forest
    clf = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    clf.fit(X)
    
    # Get anomaly scores (lower is more anomalous in sklearn, but we convert to a 0-1 probability-like confidence)
    decision_scores = clf.decision_function(X) # The lower, the more abnormal
    predictions = clf.predict(X) # -1 for outliers, 1 for inliers
    
    alerts = []
    
    for i, eid in enumerate(entity_ids):
        if predictions[i] == -1:
            # It's an anomaly. Let's calculate a fake confidence between 0.7 and 0.99 based on how low the score is
            # decision_scores are usually between -0.5 and 0 for anomalies
            score = decision_scores[i]
            confidence = min(0.99, max(0.70, 0.5 - score))
            
            # Figure out the primary reason (which feature is max compared to mean)
            mean_X = np.mean(X, axis=0)
            std_X = np.std(X, axis=0)
            std_X[std_X == 0] = 1 # Avoid div by zero
            
            z_scores = (X[i] - mean_X) / std_X
            max_feature_idx = np.argmax(z_scores)
            
            reasons = [
                "Total transaction volume is abnormally high",
                "Number of transactions is abnormally high",
                "Total call duration is abnormally high",
                "Number of unique contacts (out-degree) is abnormally high"
            ]
            
            reason = reasons[max_feature_idx]
            
            alerts.append({
                "alert_id": f"ANOM-{str(uuid.uuid4())[:8]}",
                "entity_id": eid,
                "signal_type": "Analytical Signal",
                "reason": f"ML Anomaly detected: {reason} compared to network baseline.",
                "method": "isolation_forest_score",
                "confidence": round(confidence, 2),
                "evidence": evidence_map[eid][:5] # Top 5 recent interactions
            })
            
    return alerts

if __name__ == "__main__":
    workspace_root = get_workspace_root()
    graph_path = os.path.join(workspace_root, "data", "mock_graph.json")
    graph = load_graph(graph_path)
    alerts = run_ml_engine(graph)
    print(json.dumps(alerts, indent=2))
