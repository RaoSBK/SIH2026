from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
import asyncio
import json

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

import logging

logger = logging.getLogger(__name__)

@app.post("/api/process-evidence")
async def process_evidence(files: List[UploadFile] = File(...)):
    logger.info(f"Received {len(files)} files for processing via ingestion layer.")

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

            # Run synchronous (blocking) NLP work off the event loop thread
            result = await asyncio.to_thread(
                process_file,
                temp_path,
                None,           # file_type: auto-detect from extension
                "investigator_upload",
                None,           # case_id: TODO wire from request param
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
            return json.load(f)
    except Exception:
        return []

@app.get("/api/needs-review")
def get_needs_review():
    """Returns all ambiguous entity matches pending investigator confirmation."""
    registry_path = os.path.join(os.path.dirname(__file__), "../../data/entity_registry.json")
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"entities": {}}

@app.get("/api/filtered-edges")
def get_filtered_edges():
    """
    Returns the full audit trail of every edge removed from the graph
    (self-loops, phone conflicts, etc.) with the source document reference.
    Nothing is silently deleted — supervisors can audit all dropped edges here.
    """
    path = os.path.join(os.path.dirname(__file__), "../../data/filtered_edges.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

@app.get("/api/review-queue")
def get_review_queue():
    """
    Aggregates all pending REVIEW_REQUIRED items from the entity registry.
    Used by the investigator UI to display the review queue badge and list.
    Includes: PERSON_NAME_AMBIGUITY (high-sim, no corroboration) and
              PHONE_CONFLICT (one phone → multiple distinct identities).
    """
    # The registry stores needs_review items from all past ingestion runs
    registry_path = os.path.join(os.path.dirname(__file__), "../../data/entity_registry.json")
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "pending_review": data.get("needs_review", []),
            "total": len(data.get("needs_review", [])),
        }
    except Exception:
        return {"pending_review": [], "total": 0}

