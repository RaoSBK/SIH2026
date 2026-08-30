import os
import re
import json
from cias_er.pipeline import resolve_entities

def extract_entities_from_text(file_path, doc_id):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    entities = []
    
    # Extract subjects
    # E.g. "Subject Priya Joshi was identified"
    subjects = re.findall(r"Subject\s+(.+?)\s+was", text)
    
    # Extract contact numbers
    # E.g. "Contact number 9316044204 was"
    phones = re.findall(r"Contact number\s+(\d+)\s+was", text)
    
    # Extract vehicles
    vehicles = re.findall(r"bearing plate\s+([A-Z0-9]+)\s+was", text)
    
    # For now, we will create an entity for each subject. If a document has multiple subjects 
    # and multiple phones, we might not know exactly who the phone belongs to without complex NLP.
    # We will just attach the first phone found in the document to the first subject, 
    # or create separate entities. 
    # Since ER deduplicates, let's create a node for each subject. 
    # We'll attach the phone to all subjects in the document as a heuristic, 
    # or just create a single "Document Entity Context" if we want.
    # A better approach: Each subject is an entity.
    
    for i, name in enumerate(subjects):
        phone = phones[0] if phones else ""
        entities.append({
            "id": f"{doc_id}_E{i+1}",
            "name": name.strip(),
            "phone": phone,
            "address": "", # No address in this mock FIR format
            "doc_id": doc_id
        })
        
    return entities

def process_data_folder(data_dir):
    all_entities = []
    fir_dir = os.path.join(data_dir, 'fir')
    
    if not os.path.exists(fir_dir):
        print(f"Directory not found: {fir_dir}")
        return
        
    for filename in os.listdir(fir_dir):
        if filename.endswith(".txt"):
            doc_id = filename.replace(".txt", "")
            file_path = os.path.join(fir_dir, filename)
            doc_entities = extract_entities_from_text(file_path, doc_id)
            all_entities.extend(doc_entities)
            
    print(f"Extracted {len(all_entities)} entities from {len(os.listdir(fir_dir))} FIR documents.")
    
    # Run Entity Resolution
    print("Running Entity Resolution pipeline...")
    result = resolve_entities(all_entities)
    
    # Output results
    output_path = os.path.join(data_dir, 'resolved_graph.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        
    print(f"Resolved into {len(result['clusters'])} clusters.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    process_data_folder(data_dir)
