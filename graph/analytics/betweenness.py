import networkx as nx
from typing import Dict, Any

def compute_betweenness(graph_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes Betweenness Centrality to identify bridge entities connecting communities.
    
    Returns:
        dict: {node_id: score}
    """
    nodes = graph_data.get("nodes", [])
    if not nodes:
        return {}
        
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"])
    for e in graph_data.get("edges", []):
        s = e.get("source")
        t = e.get("target")
        if s and t:
            G.add_edge(s, t)
            
    if G.number_of_nodes() == 0:
        return {}
        
    try:
        bw_scores = nx.betweenness_centrality(G)
        return {nid: round(float(score), 4) for nid, score in bw_scores.items()}
    except Exception:
        return {n["id"]: 0.0 for n in nodes}
