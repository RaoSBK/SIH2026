import json
import os
from datetime import datetime
from collections import defaultdict
import uuid

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

def run_rule_engine(graph_data):
    """
    Stage 1: Transparent, heuristic rules for anomaly detection.
    """
    alerts = []
    edges = graph_data.get("edges", [])
    
    # Organize data by entity
    tx_by_entity = defaultdict(list)
    call_by_entity = defaultdict(list)
    neighbors_by_entity = defaultdict(set)
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        ts_val = edge.get("timestamp")
        if ts_val:
            try:
                timestamp = datetime.fromisoformat(str(ts_val))
            except Exception:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        neighbors_by_entity[source].add(target)
        neighbors_by_entity[target].add(source)
        
        edge_type = str(edge.get("type", "")).upper()
        edge_id = edge.get("id", str(uuid.uuid4()))
        if edge_type in ("TRANSACTION", "TRANSFERRED_TO"):
            amount = float(edge.get("amount", edge.get("attributes", {}).get("amount", 1000)))
            tx_by_entity[source].append({"id": edge_id, "amount": amount, "time": timestamp})
        elif edge_type in ("CALL", "CALLED", "COMMUNICATED_WITH"):
            duration = float(edge.get("duration", edge.get("attributes", {}).get("duration", 60)))
            call_by_entity[source].append({"id": edge_id, "duration": duration, "time": timestamp})
            
    # Rule 1: Transaction Spike
    for entity, txs in tx_by_entity.items():
        if len(txs) < 5:
            continue
            
        # Sort by time
        txs.sort(key=lambda x: x["time"])
        
        # Calculate baseline (everything except last 7 days)
        last_tx_time = txs[-1]["time"]
        import datetime as dt
        cutoff_time = last_tx_time - dt.timedelta(days=7)
        
        baseline_txs = [tx for tx in txs if tx["time"] < cutoff_time]
        recent_txs = [tx for tx in txs if tx["time"] >= cutoff_time]
        
        if not baseline_txs or not recent_txs:
            continue
            
        baseline_avg = sum(t["amount"] for t in baseline_txs) / len(baseline_txs)
        recent_avg = sum(t["amount"] for t in recent_txs) / len(recent_txs)
        
        if baseline_avg > 0 and (recent_avg / baseline_avg) > 3.0 and len(recent_txs) >= 3:
            # Anomaly!
            increase_pct = int(((recent_avg / baseline_avg) - 1) * 100)
            alerts.append({
                "alert_id": f"ANOM-{str(uuid.uuid4())[:8]}",
                "entity_id": entity,
                "signal_type": "Analytical Signal",
                "reason": f"Transaction volume increased {increase_pct}% over past 7 days compared to baseline.",
                "method": "rule:transaction_spike",
                "confidence": 0.85,
                "evidence": [t["id"] for t in recent_txs]
            })

    # Rule 2: Communication Spike
    for entity, calls in call_by_entity.items():
        if len(calls) < 5:
            continue
            
        calls.sort(key=lambda x: x["time"])
        import datetime as dt
        last_call_time = calls[-1]["time"]
        cutoff_time = last_call_time - dt.timedelta(days=2)
        
        baseline_calls = [c for c in calls if c["time"] < cutoff_time]
        recent_calls = [c for c in calls if c["time"] >= cutoff_time]
        
        if not baseline_calls or not recent_calls:
            continue
            
        baseline_freq = len(baseline_calls) / max(1, (cutoff_time - calls[0]["time"]).days)
        recent_freq = len(recent_calls) / 2.0 # 2 days window
        
        if baseline_freq > 0 and (recent_freq / baseline_freq) > 5.0 and len(recent_calls) >= 10:
            increase_pct = int(((recent_freq / baseline_freq) - 1) * 100)
            alerts.append({
                "alert_id": f"ANOM-{str(uuid.uuid4())[:8]}",
                "entity_id": entity,
                "signal_type": "Analytical Signal",
                "reason": f"Communication frequency increased {increase_pct}% in a short window.",
                "method": "rule:communication_spike",
                "confidence": 0.80,
                "evidence": [c["id"] for c in recent_calls[-5:]] # top 5 recent calls
            })
            
    # Rule 3: Bridge Node Heuristic (simplified for mock graph)
    # If an entity suddenly forms connections with nodes that have zero overlap with its previous neighborhood
    for entity, calls in call_by_entity.items():
        if len(calls) < 4:
            continue
            
        import datetime as dt
        calls.sort(key=lambda x: x["time"])
        last_call_time = calls[-1]["time"]
        cutoff_time = last_call_time - dt.timedelta(days=2)
        
        # Get historical neighbors vs recent neighbors (from edges directly)
        hist_neighbors = set()
        recent_neighbors = set()
        
        recent_evidence = []
        for edge in edges:
            if edge["source"] == entity or edge["target"] == entity:
                other = edge["target"] if edge["source"] == entity else edge["source"]
                edge_time = datetime.fromisoformat(edge["timestamp"])
                
                if edge_time < cutoff_time:
                    hist_neighbors.add(other)
                else:
                    recent_neighbors.add(other)
                    if edge["type"] == "CALL":
                        recent_evidence.append(edge["id"])
                        
        # If recent neighbors are completely disjoint from hist neighbors and there are multiple
        if hist_neighbors and len(recent_neighbors - hist_neighbors) >= 3:
            alerts.append({
                "alert_id": f"ANOM-{str(uuid.uuid4())[:8]}",
                "entity_id": entity,
                "signal_type": "Analytical Signal",
                "reason": f"Entity rapidly connected to {len(recent_neighbors - hist_neighbors)} new, previously disconnected entities.",
                "method": "rule:bridge_node",
                "confidence": 0.75,
                "evidence": recent_evidence[:5]
            })

    return alerts

if __name__ == "__main__":
    workspace_root = get_workspace_root()
    graph_path = os.path.join(workspace_root, "data", "mock_graph.json")
    graph = load_graph(graph_path)
    alerts = run_rule_engine(graph)
    print(json.dumps(alerts, indent=2))
