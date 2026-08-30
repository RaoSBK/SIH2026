import json
import os
from cias_er.pipeline import resolve_entities

def test_pipeline():
    curr_dir = os.path.dirname(__file__)
    with open(os.path.join(curr_dir, 'synthetic_data.json'), 'r') as f:
        data = json.load(f)
        
    result = resolve_entities(data)
    
    nodes = result['nodes']
    links = result['links']
    clusters = result['clusters']
    
    print("Nodes:", json.dumps(nodes, indent=2))
    print("Links:", json.dumps(links, indent=2))
    print("Clusters Summary:", json.dumps(clusters, indent=2))
    
    # Validation 1: E1 and E2 should have a solid link (Same phone, similar name)
    solid_links = [l for l in links if ((l['source'] == 'E1' and l['target'] == 'E2') or (l['source'] == 'E2' and l['target'] == 'E1')) and l['line_type'] == 'solid']
    assert len(solid_links) > 0, "E1 and E2 should have a solid link"
    
    # Validation 2: E1 and E5 should have a dotted link (Same name, different identifiers -> ambiguous)
    dotted_links = [l for l in links if ((l['source'] == 'E1' and l['target'] == 'E5') or (l['source'] == 'E5' and l['target'] == 'E1')) and l['line_type'] == 'dotted']
    assert len(dotted_links) > 0, "E1 and E5 should have a dotted link"
    
    # Validation 3: Don Dawood (E4) should map to the mock historical database
    dawood = next(n for n in nodes if n['id'] == 'E4')
    assert dawood['historical_firs'] == 12, "Don Dawood should have 12 historical FIRs"
    assert dawood['risk_color'] == 'red', "Don Dawood should have a red risk color"
    
    # Validation 4: E3 (Ravikant) should have 5 FIRs and orange risk
    ravikant = next(n for n in nodes if n['id'] == 'E3')
    assert ravikant['historical_firs'] == 5, "Ravikant should have 5 historical FIRs"
    assert ravikant['risk_color'] == 'orange', "Ravikant should have an orange risk color"
    
    print("\n[SUCCESS] All pipeline validations passed!")

if __name__ == '__main__':
    test_pipeline()
