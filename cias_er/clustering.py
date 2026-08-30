# Dummy database mapping for the mock criminal history lookup
CRIMINAL_DB = {
    "ravi kumar": {"firs": 2, "risk": "yellow"},
    "r kumar": {"firs": 2, "risk": "yellow"},
    "ravikant": {"firs": 5, "risk": "orange"},
    "don dawood": {"firs": 12, "risk": "red"}
}

def check_criminal_history(name: str) -> dict:
    """
    Simulates a database lookup for historical FIRs and risk level.
    Returns a dict with 'firs' (int) and 'risk_color' (str: none, yellow, orange, red).
    """
    if not name:
        return {"firs": 0, "risk_color": "none"}
    
    n_lower = str(name).lower().strip()
    if n_lower in CRIMINAL_DB:
        return {"firs": CRIMINAL_DB[n_lower]["firs"], "risk_color": CRIMINAL_DB[n_lower]["risk"]}
        
    return {"firs": 0, "risk_color": "none"}

def build_clusters(entities: list, scores_matrix: dict, threshold_high=0.85, threshold_low=0.5):
    """
    Builds the graph nodes and links based on pairwise scores.
    Uses Connected Components to resolve clusters.
    """
    nodes = []
    links = []
    
    # Disjoint-set data structure for connected components
    parent = {e['id']: e['id'] for e in entities}
    
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
        
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    # Add edges and unify clusters
    for (id_a, id_b), conf in scores_matrix.items():
        if conf >= threshold_low:
            union(id_a, id_b)
            # Create a link for the frontend graph visualization
            # Dotted lines indicate ambiguity and require user consent
            line_type = "solid" if conf >= threshold_high else "dotted"
            links.append({
                "source": id_a,
                "target": id_b,
                "confidence": round(conf, 3),
                "line_type": line_type
            })
            
    # Group entities into their resolved clusters
    clusters_map = {}
    for e in entities:
        c_id = find(e['id'])
        if c_id not in clusters_map:
            clusters_map[c_id] = []
        clusters_map[c_id].append(e['id'])
        
    # Build the final nodes with history data
    for e in entities:
        history = check_criminal_history(e.get('name', ''))
        c_id = find(e['id'])
        cluster_members = clusters_map[c_id]
        
        # If ANY internal link in this entity's cluster is dotted, the entire cluster needs review
        needs_review = False
        for link in links:
            if (link['source'] in cluster_members or link['target'] in cluster_members) and link['line_type'] == "dotted":
                needs_review = True
                break
                
        nodes.append({
            "id": e['id'],
            "name": e.get('name', ''),
            "cluster_id": c_id,
            "status": "REVIEW_REQUIRED" if needs_review else "HIGH_CONFIDENCE",
            "historical_firs": history["firs"],
            "risk_color": history["risk_color"],
            "raw_data": e
        })
        
    # Prepare summary
    clusters_summary = []
    for k, v in clusters_map.items():
        c_status = "REVIEW_REQUIRED" if any(n['status'] == 'REVIEW_REQUIRED' for n in nodes if n['id'] in v) else "HIGH_CONFIDENCE"
        clusters_summary.append({
            "cluster_id": k,
            "members": v,
            "status": c_status
        })

    return {
        "nodes": nodes,
        "links": links,
        "clusters": clusters_summary
    }
