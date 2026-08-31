from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil

from .ingestion.service import process_file

app = FastAPI(title="CIAS ML Backend")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local dev — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "CIAS ML Backend"}

@app.post("/api/process-evidence")
async def process_evidence(files: List[UploadFile] = File(...)):
    print(f"Received {len(files)} files for processing via ingestion layer.")

    global_nodes = {}
    global_links = []
    statuses = []
    all_needs_review = []

    os.makedirs("temp_uploads", exist_ok=True)

    for file in files:
        temp_path = os.path.join("temp_uploads", file.filename)

        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            result = process_file(
                file_path=temp_path,
                source_label="investigator_upload"
            )

            statuses.append({
                "filename": file.filename,
                "status": result["status"],
                "message": result.get("message"),
                "resolution_stats": result.get("resolution_stats", {})
            })

            if result["status"] == "success":
                data = result.get("data", {"nodes": [], "links": []})
                for n in data["nodes"]:
                    global_nodes[n["id"]] = n
                global_links.extend(data["links"])
                all_needs_review.extend(result.get("needs_review", []))

        except Exception as e:
            statuses.append({"filename": file.filename, "status": "error", "message": str(e)})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Deduplicate links
    unique_links = []
    seen = set()
    for l in global_links:
        h = f"{l['source']}-{l['target']}-{l['type']}"
        if h not in seen:
            seen.add(h)
            unique_links.append(l)

    # Anomaly Detection: Flag nodes with suspicious levels of connectivity
    degrees = {n_id: 0 for n_id in global_nodes}
    for l in unique_links:
        if l['source'] in degrees: degrees[l['source']] += 1
        if l['target'] in degrees: degrees[l['target']] += 1
        
    for n_id, n in global_nodes.items():
        if degrees[n_id] >= 3:
            n['status'] = 'REVIEW_REQUIRED'
            n['risk_color'] = 'orange'
        else:
            n['risk_color'] = 'none'
            
        if degrees[n_id] >= 5:
            n['risk_color'] = 'red'
            n['historical_firs'] = 1

    return {
        "nodes": list(global_nodes.values()),
        "links": unique_links,
        "ingestion_statuses": statuses,
        "needs_review": all_needs_review
    }

@app.get("/api/ingestion-audit")
def get_ingestion_audit():
    """Returns the ingestion audit log for the data history UI screen."""
    audit_path = os.path.join(os.path.dirname(__file__), "../../data/ingestion_audit.json")
    try:
        with open(audit_path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except Exception:
        return []

@app.get("/api/needs-review")
def get_needs_review():
    """Returns all ambiguous entity matches pending investigator confirmation."""
    registry_path = os.path.join(os.path.dirname(__file__), "../../data/entity_registry.json")
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except Exception:
        return {"entities": {}}
