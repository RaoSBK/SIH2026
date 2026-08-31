import os
import subprocess
import shutil

def main():
    # Directories
    base_dir = "data/synthetic/training"
    spacy_dir = os.path.join(base_dir, "spacy")
    models_out_dir = os.path.join(base_dir, "models")
    final_model_dir = "ml/nlp/models/fine_tuned"
    
    config_path = os.path.join(base_dir, "base_config.cfg")
    full_config_path = os.path.join(base_dir, "config.cfg")
    
    # 1. Initialize base config
    print("Initializing spaCy config...")
    subprocess.run([
        "python", "-m", "spacy", "init", "config", config_path, 
        "--lang", "en", 
        "--pipeline", "ner", 
        "--optimize", "efficiency",
        "--force"
    ], check=True)
    
    # 2. Fill config
    print("Filling spaCy config...")
    subprocess.run([
        "python", "-m", "spacy", "init", "fill-config", config_path, full_config_path
    ], check=True)
    
    # 3. Train model
    print("Training NER model (this may take a few minutes depending on CPU/GPU)...")
    subprocess.run([
        "python", "-m", "spacy", "train", full_config_path,
        "--output", models_out_dir,
        "--paths.train", os.path.join(spacy_dir, "train.spacy"),
        "--paths.dev", os.path.join(spacy_dir, "dev.spacy")
    ], check=True)
    
    # 4. Copy best model to final destination
    print(f"Copying best model to {final_model_dir}...")
    best_model_path = os.path.join(models_out_dir, "model-best")
    
    if os.path.exists(final_model_dir):
        shutil.rmtree(final_model_dir)
        
    shutil.copytree(best_model_path, final_model_dir)
    print("Training complete and model deployed!")

if __name__ == "__main__":
    main()
