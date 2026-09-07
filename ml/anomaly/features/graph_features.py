from collections import defaultdict
from typing import Dict, Any

def extract_graph_features(graph_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extracts topological graph indicators for each node in graph_data.
    
    Returns:
        dict: {node_id: {"in_degree": val, "out_degree": val, "total_degree": val, ...}}
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])
    
    in_degrees = defaultdict(int)
    out_degrees = defaultdict(int)
    unique_targets = defaultdict(set)
    unique_sources = defaultdict(set)
    
    # Pre-populate all nodes
    for nid in nodes:
        in_degrees[nid] = 0
        out_degrees[nid] = 0
        
    for edge in edges:
        s = edge.get("source")
        t = edge.get("target")
        if not s or not t:
            continue
            
        out_degrees[s] += 1
        in_degrees[t] += 1
        unique_targets[s].add(t)
        unique_sources[t].add(s)
        
    all_node_ids = set(nodes.keys()).union(out_degrees.keys()).union(in_degrees.keys())
    features = {}
    
    for nid in all_node_ids:
        in_deg = float(in_degrees[nid])
        out_deg = float(out_degrees[nid])
        tot_deg = in_deg + out_deg
        neighbors = len(unique_targets[nid].union(unique_sources[nid]))
        ratio = out_deg / (in_deg + 1.0)
        
        features[nid] = {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": tot_deg,
            "unique_neighbors": float(neighbors),
            "degree_ratio": round(ratio, 4)
        }
        
    return features
