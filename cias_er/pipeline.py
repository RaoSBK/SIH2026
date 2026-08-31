import json
from .matcher import score_pair
from .clustering import build_clusters

def resolve_entities(entities_input, threshold_high=0.85, threshold_low=0.5):
    """
    Main entry point for the CIAS Entity Resolution module.
    Expects a JSON string or a list of dictionaries, each with at least:
    - id
    - name
    - phone (optional)
    - address (optional)
    - doc_id (optional)
    
    Returns a dictionary containing the resolved nodes, links (with confidence and line_type),
    and the final clusters.
    """
    if isinstance(entities_input, str):
        entities = json.loads(entities_input)
    else:
        entities = entities_input
        
    scores_matrix = {}
    
    # Pairwise comparisons. 
    # NOTE: For production scale, replace this O(N^2) loop with a blocking strategy 
    # (e.g., block by first letter of last name, or Soundex).
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            e_a = entities[i]
            e_b = entities[j]
            
            # Compute confidence score
            score = score_pair(e_a, e_b)
            
            # Only record if there's some non-zero similarity
            if score > 0.0:
                scores_matrix[(e_a['id'], e_b['id'])] = score
                
    # Build graph and resolve clusters
    result = build_clusters(entities, scores_matrix, threshold_high, threshold_low)
    
    return result
