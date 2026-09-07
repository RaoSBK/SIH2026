import uuid
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any, Tuple

from ..features.graph_features import extract_graph_features
from ..features.transaction_features import extract_transaction_features
from ..features.communication_features import extract_communication_features
from .isolation_forest import IsolationForestAnomalyModel

FEATURE_NAMES = [
    "in_degree", "out_degree", "total_degree", "unique_neighbors", "degree_ratio",
    "tx_out_count", "tx_in_count", "tx_total_volume", "tx_avg_amount", "tx_max_amount", "tx_velocity",
    "call_out_count", "call_in_count", "call_total_duration", "call_avg_duration", "call_max_duration"
]

FEATURE_EXPLANATIONS = {
    "in_degree": "Incoming connection count is abnormally high",
    "out_degree": "Outgoing connection count is abnormally high",
    "total_degree": "Total degree centrality is abnormally high",
    "unique_neighbors": "Number of unique contact targets is abnormally high",
    "degree_ratio": "Out/in degree ratio is skewed",
    "tx_out_count": "Number of outgoing transactions is abnormally high",
    "tx_in_count": "Number of incoming transactions is abnormally high",
    "tx_total_volume": "Total transaction volume is abnormally high",
    "tx_avg_amount": "Average transaction amount is abnormally high",
    "tx_max_amount": "Maximum single transaction amount is abnormally high",
    "tx_velocity": "Financial velocity is abnormally high",
    "call_out_count": "Outgoing call frequency is abnormally high",
    "call_in_count": "Incoming call frequency is abnormally high",
    "call_total_duration": "Total call duration is abnormally high",
    "call_avg_duration": "Average call length is abnormally high",
    "call_max_duration": "Maximum single call duration is abnormally high"
}

def build_feature_matrix(graph_data: Dict[str, Any]) -> Tuple[List[str], np.ndarray, List[str], Dict[str, List[str]]]:
    """
    Combines topological, financial, and communication features into a feature matrix X.
    """
    g_feats = extract_graph_features(graph_data)
    t_feats = extract_transaction_features(graph_data)
    c_feats = extract_communication_features(graph_data)
    
    all_nodes = set(g_feats.keys()).union(t_feats.keys()).union(c_feats.keys())
    entity_ids = sorted(list(all_nodes))
    
    evidence_map = defaultdict(list)
    for edge in graph_data.get("edges", []):
        s = edge.get("source")
        t = edge.get("target")
        if s:
            edge_id = edge.get("id", str(uuid.uuid4()))
            evidence_map[s].append(edge_id)
            
    matrix_rows = []
    for eid in entity_ids:
        row = []
        g = g_feats.get(eid, {})
        t = t_feats.get(eid, {})
        c = c_feats.get(eid, {})
        
        row.append(g.get("in_degree", 0.0))
        row.append(g.get("out_degree", 0.0))
        row.append(g.get("total_degree", 0.0))
        row.append(g.get("unique_neighbors", 0.0))
        row.append(g.get("degree_ratio", 0.0))
        
        row.append(t.get("tx_out_count", 0.0))
        row.append(t.get("tx_in_count", 0.0))
        row.append(t.get("tx_total_volume", 0.0))
        row.append(t.get("tx_avg_amount", 0.0))
        row.append(t.get("tx_max_amount", 0.0))
        row.append(t.get("tx_velocity", 0.0))
        
        row.append(c.get("call_out_count", 0.0))
        row.append(c.get("call_in_count", 0.0))
        row.append(c.get("call_total_duration", 0.0))
        row.append(c.get("call_avg_duration", 0.0))
        row.append(c.get("call_max_duration", 0.0))
        
        matrix_rows.append(row)
        
    X = np.array(matrix_rows) if matrix_rows else np.empty((0, len(FEATURE_NAMES)))
    return entity_ids, X, FEATURE_NAMES, evidence_map

def score_graph_anomalies(graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Executes feature matrix extraction and Isolation Forest scoring.
    """
    entity_ids, X, feature_names, evidence_map = build_feature_matrix(graph_data)
    
    if len(entity_ids) == 0 or X.shape[0] == 0:
        return []
        
    model = IsolationForestAnomalyModel(n_estimators=100, contamination=0.05, random_state=42)
    preds, confidences = model.fit_predict_confidence(X)
    
    mean_X = np.mean(X, axis=0)
    std_X = np.std(X, axis=0)
    std_X[std_X == 0] = 1.0
    
    alerts = []
    for i, eid in enumerate(entity_ids):
        if preds[i] == -1:
            z_scores = (X[i] - mean_X) / std_X
            max_idx = int(np.argmax(z_scores))
            feat_name = feature_names[max_idx]
            reason_text = FEATURE_EXPLANATIONS.get(feat_name, "Behavior is anomalous compared to baseline.")
            
            alerts.append({
                "alert_id": f"ANOM-{str(uuid.uuid4())[:8]}",
                "entity_id": eid,
                "signal_type": "Analytical Signal",
                "reason": f"ML Anomaly detected: {reason_text}.",
                "method": "isolation_forest_score",
                "confidence": confidences[i],
                "evidence": evidence_map[eid][:5]
            })
            
    return alerts
