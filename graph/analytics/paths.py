import networkx as nx
from typing import Dict, List, Any, Optional

def find_shortest_path(graph_data: Dict[str, Any], source_id: str, target_id: str) -> Dict[str, Any]:
    """
    Finds the shortest network path sequence and distance between source and target entities.
    
    Returns:
        dict: {
            "found": True/False,
            "distance": int,
            "path": ["node_1", "node_2", "node_3"],
            "edges": [{"source": "node_1", "target": "node_2", ...}]
        }
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    if source_id not in nodes or target_id not in nodes:
        return {"found": False, "distance": -1, "path": [], "edges": [], "message": "Source or target node not found."}

    G = nx.Graph()
    edge_dict = {}
    for n in nodes:
        G.add_node(n)

    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if s and t:
            G.add_edge(s, t)
            edge_dict[(s, t)] = e
            edge_dict[(t, s)] = e

    try:
        path = nx.shortest_path(G, source=source_id, target=target_id)
        path_edges = []
        for i in range(len(path) - 1):
            s = path[i]
            t = path[i+1]
            if (s, t) in edge_dict:
                path_edges.append(edge_dict[(s, t)])

        return {
            "found": True,
            "distance": len(path) - 1,
            "path": path,
            "edges": path_edges
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {
            "found": False,
            "distance": -1,
            "path": [],
            "edges": [],
            "message": f"No network path found between {source_id} and {target_id}."
        }
