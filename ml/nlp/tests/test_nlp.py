import os
import json
from ml.nlp.cias_nlp import process_text

def get_workspace_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current:
        if os.path.exists(os.path.join(current, "docker-compose.yml")) or os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return r"d:\SIH2026"

def test_on_synthetic_data(data_dir=None):
    """
    Test the NLP pipeline on 2 samples from FIRs, Surveillance, and Intelligence.
    """
    workspace_root = get_workspace_root()
    if not data_dir:
        data_dir = os.path.join(workspace_root, "data")
        
    sources = ["fir", "surveillance", "intelligence"]
    results = []
    
    for source in sources:
        source_dir = os.path.join(data_dir, source)
        if not os.path.isdir(source_dir):
            continue
            
        print(f"\n--- Processing 2 samples from {source.upper()} ---")
        
        # Grab first 2 files
        files = [f for f in os.listdir(source_dir) if f.endswith(".txt")][:2]
        
        for file_name in files:
            file_path = os.path.join(source_dir, file_name)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            doc_id = f"{source.upper()}-{file_name.replace('.txt', '')}"
            print(f"\n[Input Text]: {text.strip()}")
            
            output = process_text(text, document_id=doc_id)
            
            print(f"[Structured Output JSON]:\n{json.dumps(output, indent=2)}")
            results.append(output)
            
    # Save test results in workspace root
    output_path = os.path.join(workspace_root, "nlp_test_output.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[INFO] Saved full extraction results to {output_path}")

if __name__ == "__main__":
    test_on_synthetic_data()
