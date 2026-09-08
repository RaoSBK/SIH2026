import networkx as nx
from typing import Dict, List, Any

COMMUNITY_COLORS = [
    "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16"
]

def detect_communities(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detects modular community clusters in the graph network.
    
    Returns:
        dict: {
            "communities": {"community_1": ["node_a", "node_b"], ...},
            "node_communities": {"node_a": "community_1", ...},
            "community_colors": {"community_1": "#3B82F6", ...}
        }
    """
    nodes = graph_data.get("nodes", [])
    if not nodes:
        return {"communities": {}, "node_communities": {}, "community_colors": {}}

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"])
    for e in graph_data.get("edges", []):
        s = e.get("source")
        t = e.get("target")
        if s and t:
            G.add_edge(s, t)

    try:
        if G.number_of_edges() > 0:
            comm_sets = list(nx.community.greedy_modularity_communities(G))
        else:
            comm_sets = [set([n]) for n in G.nodes()]
    except Exception:
        comm_sets = list(nx.connected_components(G))

    communities = {}
    node_communities = {}
    community_colors = {}

    for i, comm_set in enumerate(comm_sets):
        comm_id = f"community_{i+1}"
        color = COMMUNITY_COLORS[i % len(COMMUNITY_COLORS)]
        node_list = sorted(list(comm_set))

        communities[comm_id] = node_list
        community_colors[comm_id] = color

        for nid in node_list:
            node_communities[nid] = comm_id

    return {
        "communities": communities,
        "node_communities": node_communities,
        "community_colors": community_colors
    }
