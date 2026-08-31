from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import traceback

from .ml_processor import process_pdf_files

app = FastAPI(title="Veritas ML Backend")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Veritas ML Backend"}

from .ingestion.service import process_file
import os
import shutil

@app.post("/api/process-evidence")
async def process_evidence(files: List[UploadFile] = File(...)):
    print(f"Received {len(files)} files for processing via new ingestion layer.")
    
    global_nodes = {}
    global_links = []
    statuses = []

    # Ensure temp dir exists
    os.makedirs("temp_uploads", exist_ok=True)
    
    for file in files:
        temp_path = os.path.join("temp_uploads", file.filename)
        
        try:
            # Save uploaded file to disk
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Run through universal ingestion layer
            result = process_file(
                file_path=temp_path,
                source_label="investigator_upload"
            )
            
            statuses.append({"filename": file.filename, "status": result["status"], "message": result.get("message")})
            
            if result["status"] == "success":
                # Merge graph data
                data = result.get("data", {"nodes": [], "links": []})
                for n in data["nodes"]:
                    global_nodes[n["id"]] = n
                global_links.extend(data["links"])
                
        except Exception as e:
            statuses.append({"filename": file.filename, "status": "error", "message": str(e)})
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    # Basic deduplication of links
    unique_links = []
    seen = set()
    for l in global_links:
        h = f"{l['source']}-{l['target']}-{l['type']}"
        if h not in seen:
            seen.add(h)
            unique_links.append(l)

    return {
        "nodes": list(global_nodes.values()),
        "links": unique_links,
        "ingestion_statuses": statuses
    }
