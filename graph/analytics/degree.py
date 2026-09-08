import networkx as nx
from typing import Dict, Any

def compute_degree_centrality(graph_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Computes in-degree, out-degree, and total degree centrality for graph nodes.
    
    Returns:
        dict: {node_id: {"in_degree": val, "out_degree": val, "centrality": val}}
    """
    nodes = graph_data.get("nodes", [])
    if not nodes:
        return {}

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"])
    for e in graph_data.get("edges", []):
        s = e.get("source")
        t = e.get("target")
        if s and t:
            G.add_edge(s, t)

    try:
        in_deg_cent = nx.in_degree_centrality(G)
        out_deg_cent = nx.out_degree_centrality(G)
        tot_deg_cent = nx.degree_centrality(G)
    except Exception:
        in_deg_cent = {n["id"]: 0.0 for n in nodes}
        out_deg_cent = {n["id"]: 0.0 for n in nodes}
        tot_deg_cent = {n["id"]: 0.0 for n in nodes}

    results = {}
    for n in nodes:
        nid = n["id"]
        results[nid] = {
            "in_degree": round(float(G.in_degree(nid)), 4) if nid in G else 0.0,
            "out_degree": round(float(G.out_degree(nid)), 4) if nid in G else 0.0,
            "in_degree_centrality": round(float(in_deg_cent.get(nid, 0.0)), 4),
            "out_degree_centrality": round(float(out_deg_cent.get(nid, 0.0)), 4),
            "total_degree_centrality": round(float(tot_deg_cent.get(nid, 0.0)), 4)
        }

    return results
