from collections import defaultdict
from typing import Dict, Any

def extract_transaction_features(graph_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extracts financial & transaction velocity metrics for each node in graph_data.
    
    Returns:
        dict: {node_id: {"tx_out_count": val, "tx_total_volume": val, ...}}
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])
    
    tx_out_counts = defaultdict(int)
    tx_in_counts = defaultdict(int)
    tx_volumes = defaultdict(float)
    tx_max_amounts = defaultdict(float)
    tx_amounts = defaultdict(list)
    
    for edge in edges:
        s = edge.get("source")
        t = edge.get("target")
        if not s or not t:
            continue
            
        edge_type = str(edge.get("type", "")).upper()
        if edge_type in ("TRANSACTION", "TRANSFERRED_TO", "TRANSFERRED"):
            amount = float(edge.get("amount", edge.get("attributes", {}).get("amount", 1000.0)))
            tx_out_counts[s] += 1
            tx_in_counts[t] += 1
            tx_volumes[s] += amount
            tx_amounts[s].append(amount)
            if amount > tx_max_amounts[s]:
                tx_max_amounts[s] = amount

    all_node_ids = set(nodes.keys()).union(tx_out_counts.keys()).union(tx_in_counts.keys())
    features = {}
    
    for nid in all_node_ids:
        out_cnt = float(tx_out_counts[nid])
        in_cnt = float(tx_in_counts[nid])
        tot_vol = float(tx_volumes[nid])
        max_amt = float(tx_max_amounts[nid])
        avg_amt = tot_vol / out_cnt if out_cnt > 0 else 0.0
        velocity = tot_vol / (out_cnt + 1.0)
        
        features[nid] = {
            "tx_out_count": out_cnt,
            "tx_in_count": in_cnt,
            "tx_total_volume": tot_vol,
            "tx_avg_amount": round(avg_amt, 2),
            "tx_max_amount": round(max_amt, 2),
            "tx_velocity": round(velocity, 2)
        }
        
    return features
