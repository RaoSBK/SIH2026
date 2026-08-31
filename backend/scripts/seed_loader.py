import os
import sys

# Add backend dir to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.service import process_file

def load_seeds(seed_dir: str):
    """
    Bulk loads all files in a seed directory using the universal ingestion pipeline.
    """
    print(f"Starting bulk ingestion from {seed_dir}...")
    
    if not os.path.exists(seed_dir):
        print(f"Error: Directory {seed_dir} does not exist.")
        return
        
    files = [f for f in os.listdir(seed_dir) if os.path.isfile(os.path.join(seed_dir, f))]
    
    if not files:
        print("No files found to ingest.")
        return
        
    success_count = 0
    
    for filename in files:
        filepath = os.path.join(seed_dir, filename)
        print(f"\nProcessing {filename}...")
        
        result = process_file(
            file_path=filepath,
            source_label="seed_loader",
            case_id="SEED_DATA"
        )
        
        if result["status"] == "success":
            success_count += 1
            print(f"  [OK] Extracted {result['new_nodes']} entities and {result['relationships_created']} relationships.")
        else:
            print(f"  [ERROR] Stage: {result.get('stage')} - {result.get('message')}")
            
    print(f"\nIngestion Complete: {success_count}/{len(files)} files processed successfully.")

if __name__ == "__main__":
    # Test directory relative to project root
    test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
    load_seeds(test_data_dir)
