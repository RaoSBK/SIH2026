import os
import json
from cias_nlp import process_text

def test_on_synthetic_data(data_dir=r"c:\Users\sahid\Desktop\SIH\data"):
    """
    Test the NLP pipeline on 5 samples from FIRs, Surveillance, and Intelligence.
    """
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
            
    # Save test results
    with open(r"c:\Users\sahid\Desktop\SIH\nlp_test_output.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n[INFO] Saved full extraction results to nlp_test_output.json")

if __name__ == "__main__":
    test_on_synthetic_data()
