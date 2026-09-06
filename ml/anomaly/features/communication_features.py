from collections import defaultdict
from typing import Dict, Any

def extract_communication_features(graph_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extracts call & communication metrics for each node in graph_data.
    
    Returns:
        dict: {node_id: {"call_out_count": val, "call_total_duration": val, ...}}
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])
    
    call_out_counts = defaultdict(int)
    call_in_counts = defaultdict(int)
    call_durations = defaultdict(float)
    call_max_durations = defaultdict(float)
    
    for edge in edges:
        s = edge.get("source")
        t = edge.get("target")
        if not s or not t:
            continue
            
        edge_type = str(edge.get("type", "")).upper()
        if edge_type in ("CALL", "CALLED", "COMMUNICATED_WITH", "CALLING"):
            duration = float(edge.get("duration", edge.get("attributes", {}).get("duration", 60.0)))
            call_out_counts[s] += 1
            call_in_counts[t] += 1
            call_durations[s] += duration
            if duration > call_max_durations[s]:
                call_max_durations[s] = duration

    all_node_ids = set(nodes.keys()).union(call_out_counts.keys()).union(call_in_counts.keys())
    features = {}
    
    for nid in all_node_ids:
        out_cnt = float(call_out_counts[nid])
        in_cnt = float(call_in_counts[nid])
        tot_dur = float(call_durations[nid])
        max_dur = float(call_max_durations[nid])
        avg_dur = tot_dur / out_cnt if out_cnt > 0 else 0.0
        
        features[nid] = {
            "call_out_count": out_cnt,
            "call_in_count": in_cnt,
            "call_total_duration": tot_dur,
            "call_avg_duration": round(avg_dur, 2),
            "call_max_duration": round(max_dur, 2)
        }
        
    return features
