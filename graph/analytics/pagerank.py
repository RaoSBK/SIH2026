import networkx as nx
from typing import Dict, Any

def build_networkx_graph(graph_data: Dict[str, Any], directed: bool = True) -> nx.Graph:
    """Helper to convert graph dictionary into NetworkX graph object."""
    G = nx.DiGraph() if directed else nx.Graph()
    
    for n in graph_data.get("nodes", []):
        G.add_node(n["id"], **n)
        
    for e in graph_data.get("edges", []):
        s = e.get("source")
        t = e.get("target")
        if s and t:
            G.add_edge(s, t, **e)
            
    return G

def compute_pagerank(graph_data: Dict[str, Any], alpha: float = 0.85) -> Dict[str, float]:
    """
    Computes PageRank centrality for all nodes in graph_data.
    
    Returns:
        dict: {node_id: score}
    """
    nodes = graph_data.get("nodes", [])
    if not nodes:
        return {}
        
    G = build_networkx_graph(graph_data, directed=True)
    if G.number_of_nodes() == 0:
        return {}
        
    try:
        pr_scores = nx.pagerank(G, alpha=alpha)
        return {nid: round(float(score), 4) for nid, score in pr_scores.items()}
    except Exception:
        # Fallback uniform score
        n_nodes = G.number_of_nodes()
        return {nid: round(1.0 / max(1, n_nodes), 4) for nid in G.nodes()}
