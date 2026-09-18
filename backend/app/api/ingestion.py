# -*- coding: utf-8 -*-

from fastapi import APIRouter, UploadFile, File, Form, Depends, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import os
import shutil
import asyncio
import logging
import uuid
from datetime import datetime

from backend.app.auth.rbac import get_current_user
from backend.app.users.models import User
from backend.app.database.postgres import get_db
from backend.app.ingestion.service import process_file
from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# Global in-memory job registry & WebSocket connection pools
PIPELINE_JOBS: Dict[str, Dict[str, Any]] = {}
WEBSOCKET_CLIENTS: Dict[str, List[WebSocket]] = {}

async def notify_job_progress(job_id: str, stage: int, stage_name: str, message: str, status: str = "running", data: dict = None):
    job = PIPELINE_JOBS.get(job_id)
    if not job:
        return
    job["stage"] = stage
    job["stage_name"] = stage_name
    job["status"] = status
    log_entry = {
        "stage": stage,
        "stage_name": stage_name,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    job["logs"].append(log_entry)
    if data is not None:
        job["result"] = data

    payload = {
        "job_id": job_id,
        "status": status,
        "stage": stage,
        "stage_name": stage_name,
        "message": message,
        "logs": job["logs"],
        "result": data
    }

    clients = WEBSOCKET_CLIENTS.get(job_id, [])
    stale = []
    for ws in clients:
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        if ws in clients:
            clients.remove(ws)

async def run_pipeline_job(job_id: str, saved_files: List[Dict[str, Any]], case_id: str):
    try:
        # Stage 0: Ingest
        await notify_job_progress(job_id, 0, "Ingest", f"Ingesting {len(saved_files)} source document(s)...")
        await asyncio.sleep(0.1)

        # Stage 1: Normalize
        await notify_job_progress(job_id, 1, "Normalize", "Normalizing names, phone numbers and account identifiers...")
        await asyncio.sleep(0.1)

        # Stage 2: Extract (Parallel parsing & NER extraction using asyncio.gather)
        await notify_job_progress(job_id, 2, "Extract", "Running multilingual NER & pattern extraction...")

        tasks = [
            asyncio.to_thread(process_file, item["path"], None, "investigator_upload", case_id)
            for item in saved_files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        global_nodes = {}
        global_links = []
        statuses = []
        all_needs_review = []

        for item, res in zip(saved_files, results):
            if isinstance(res, Exception):
                statuses.append({"filename": item["filename"], "status": "error", "message": str(res)})
            else:
                statuses.append({
                    "filename": item["filename"],
                    "status": res.get("status"),
                    "message": res.get("message"),
                    "resolution_stats": res.get("resolution_stats", {})
                })
                if res.get("status") == "success":
                    data = res.get("data", {"nodes": [], "links": []})
                    for n in data.get("nodes", []):
                        global_nodes[n["id"]] = n
                    global_links.extend(data.get("links", []))
                    all_needs_review.extend(res.get("needs_review", []))

        # Stage 3: Resolve
        await notify_job_progress(job_id, 3, "Resolve", "Resolving entities and building disambiguation payload...")

        # Deduplicate links and normalize relationship_type
        unique_links = []
        seen = set()
        for l in global_links:
            h = f"{l['source']}-{l['target']}-{l['type']}"
            if h not in seen:
                seen.add(h)
                if "relationship_type" not in l or not l["relationship_type"]:
                    l["relationship_type"] = "calling" if str(l.get("type", "")).upper() in ("CALLED", "CALL", "CALLING") else l.get("type", "")
                unique_links.append(l)

        # Phone attribute propagation
        for n_id, node in global_nodes.items():
            if node.get("type") in ("PHONE", "Phone"):
                node["phone"] = node.get("value") or node.get("name") or n_id

        for l in unique_links:
            s_node = global_nodes.get(l["source"])
            t_node = global_nodes.get(l["target"])
            if s_node and t_node:
                if (s_node.get("type") in ("PERSON", "Person")) and (t_node.get("type") in ("PHONE", "Phone")):
                    if not s_node.get("phone"):
                        s_node["phone"] = t_node.get("value") or t_node.get("name")
                elif (t_node.get("type") in ("PERSON", "Person")) and (s_node.get("type") in ("PHONE", "Phone")):
                    if not t_node.get("phone"):
                        t_node["phone"] = s_node.get("value") or s_node.get("name")

        # Evidence scoring & trail
        node_evidence_types = {}
        node_evidence_entries = {}

        for n_id, node in global_nodes.items():
            ev_types = set()
            ev_entries = []
            for sf in node.get("source_files", []) or []:
                sf_lower = sf.lower()
                if "fir" in sf_lower:
                    ev_types.add("FIR Record")
                    ev_entries.append(f"Named in First Information Report: {sf}")
                elif "cdr" in sf_lower:
                    ev_types.add("Call Data Record")
                    ev_entries.append(f"Appears in Call Data Record (CDR): {sf}")
                elif "bank" in sf_lower or "txn" in sf_lower or "statement" in sf_lower:
                    ev_types.add("Banking Ledger")
                    ev_entries.append(f"Linked to financial transaction statement: {sf}")
                elif "surveillance" in sf_lower or "intel" in sf_lower:
                    ev_types.add("Surveillance Intelligence")
                    ev_entries.append(f"Implicated in surveillance profiling report: {sf}")
                elif "interrogation" in sf_lower:
                    ev_types.add("Interrogation Summary")
                    ev_entries.append(f"Referenced during suspect interrogation: {sf}")
                else:
                    ev_types.add("Document Evidence")
                    ev_entries.append(f"Extracted from source file: {sf}")

            node_evidence_types[n_id] = ev_types
            node_evidence_entries[n_id] = ev_entries

        for l in unique_links:
            ev = l.get("evidence")
            l_type = str(l.get("type", "")).upper()
            for nid in (l["source"], l["target"]):
                if nid in global_nodes:
                    if l_type in ("CALLED", "CALL", "CALLING"):
                        node_evidence_types[nid].add("Call Data Record")
                        if ev and ev not in node_evidence_entries[nid]:
                            node_evidence_entries[nid].append(f"CDR: {ev}")
                    elif l_type in ("TRANSFERRED_TO", "TRANSACTION", "TRANSFERRED"):
                        node_evidence_types[nid].add("Banking Ledger")
                        if ev and ev not in node_evidence_entries[nid]:
                            node_evidence_entries[nid].append(f"Bank Transaction: {ev}")
                    elif ev and ev not in node_evidence_entries[nid]:
                        node_evidence_entries[nid].append(f"Relationship ({l.get('type')}): {ev}")

        for n_id, node in global_nodes.items():
            ev_types = node_evidence_types.get(n_id, set())
            ev_entries = node_evidence_entries.get(n_id, [])
            node["evidence_trail"] = ev_entries

            if len(ev_types) >= 2 or len(ev_entries) >= 3:
                node["flagged"] = True
                node["status"] = "REVIEW_REQUIRED"
                node["risk_color"] = "red"
                node["historical_firs"] = max(1, len(ev_types))
                node.setdefault("anomaly_reasons", []).append(
                    f"Repeatedly implicated across {len(ev_types)} distinct evidence types ({', '.join(sorted(ev_types))})."
                )

        # Stage 4: Graph (Batched Neo4j writes using UNWIND)
        await notify_job_progress(job_id, 4, "Graph", f"Building knowledge graph — {len(global_nodes)} nodes, {len(unique_links)} relationships.")

        try:
            from backend.app.database.neo4j import insert_graph_data
            await asyncio.to_thread(insert_graph_data, list(global_nodes.values()), unique_links, "pipeline_batch", case_id)
        except Exception as e:
            logger.error(f"Failed to persist graph to Neo4j in job {job_id}: {e}")

        # Stage 5: Analyze
        await notify_job_progress(job_id, 5, "Analyze", "Analyzing subnetworks for high-risk flags...")
        graph_payload = {"nodes": list(global_nodes.values()), "edges": unique_links}
        try:
            rule_alerts = run_rule_engine(graph_payload)
            ml_alerts = run_ml_engine(graph_payload)
            all_alerts = rule_alerts + ml_alerts

            from backend.app.api.anomaly import save_anomaly_alerts, load_stored_anomaly_alerts
            existing_alerts = load_stored_anomaly_alerts()
            existing_ids = {a.get("alert_id") for a in existing_alerts if a.get("alert_id")}
            new_unique = [a for a in all_alerts if a.get("alert_id") not in existing_ids]
            save_anomaly_alerts((new_unique + existing_alerts)[:200])

            for alert in all_alerts:
                ent_id = alert.get("entity_id")
                if ent_id in global_nodes:
                    node = global_nodes[ent_id]
                    node["flagged"] = True
                    node.setdefault("anomaly_reasons", []).append(alert.get("reason"))
                    if alert.get("reason") not in (node.get("evidence_trail") or []):
                        node.setdefault("evidence_trail", []).append(f"Anomaly Alert: {alert.get('reason')}")
                    conf = alert.get("confidence", 0.7)
                    if conf >= 0.8:
                        node["status"] = "REVIEW_REQUIRED"
                        node["risk_color"] = "red"
                        node["historical_firs"] = max(1, node.get("historical_firs", 1))
                    elif node.get("risk_color") != "red":
                        node["status"] = "REVIEW_REQUIRED"
                        node["risk_color"] = "orange"
        except Exception as e:
            logger.warning(f"Anomaly detection engine warning in job {job_id}: {e}")

        # Fallback connectivity baseline
        degrees = {n_id: 0 for n_id in global_nodes}
        for l in unique_links:
            if l['source'] in degrees: degrees[l['source']] += 1
            if l['target'] in degrees: degrees[l['target']] += 1

        for n_id, n in global_nodes.items():
            if "risk_color" not in n or n["risk_color"] == "none":
                if degrees[n_id] >= 5:
                    n['status'] = 'REVIEW_REQUIRED'
                    n['risk_color'] = 'red'
                    n['flagged'] = True
                    n['historical_firs'] = 1
                elif degrees[n_id] >= 3:
                    n['status'] = 'REVIEW_REQUIRED'
                    n['risk_color'] = 'orange'
                    n['flagged'] = True
                else:
                    n['risk_color'] = 'none'
                    n['flagged'] = False

        # Stage 6: Explain
        await notify_job_progress(job_id, 6, "Explain", "Explainability layer attached — indicators generated.")
        await asyncio.sleep(0.1)

        # Stage 7: Complete
        final_result = {
            "nodes": list(global_nodes.values()),
            "links": unique_links,
            "ingestion_statuses": statuses,
            "needs_review": all_needs_review
        }
        await notify_job_progress(job_id, 7, "Explain", "Pipeline completed. Awaiting investigator review.", status="completed", data=final_result)

    except Exception as e:
        logger.error(f"Pipeline job {job_id} failed: {e}")
        await notify_job_progress(job_id, 7, "Error", f"Pipeline execution failed: {str(e)}", status="error")
    finally:
        for item in saved_files:
            if os.path.exists(item["path"]):
                try:
                    os.remove(item["path"])
                except Exception:
                    pass

@router.post("/process-evidence")
async def process_evidence(
    files: List[UploadFile] = File(...),
    case_id: str = Form("CASE-102"),
    sync: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Received {len(files)} files for processing via ingestion layer. Case: {case_id}")

    # Auto-create case if it doesn't exist
    from backend.app.cases.repository import get_case
    from backend.app.cases.service import create_case
    from backend.app.cases.schemas import CaseCreate

    existing_case = get_case(db, case_id)
    if not existing_case:
        new_case_data = CaseCreate(case_id=case_id, title=f"Auto-generated Case {case_id}", description="Created during ingestion")
        create_case(db, new_case_data, current_user.id)

    os.makedirs("temp_uploads", exist_ok=True)
    from backend.app.evidence.service import upload_evidence

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    saved_files = []

    for file in files:
        temp_path = os.path.join("temp_uploads", f"{uuid.uuid4().hex[:4]}_{file.filename}")
        file_bytes = await file.read()
        with open(temp_path, "wb") as buffer:
            buffer.write(file_bytes)

        evidence_id = f"EV-{uuid.uuid4().hex[:8].upper()}"
        try:
            upload_evidence(
                db=db,
                file_bytes=file_bytes,
                evidence_id=evidence_id,
                case_id=case_id,
                file_name=file.filename,
                user_id=current_user.id
            )
        except Exception as e:
            logger.warning(f"Could not persist evidence {file.filename} to Postgres: {e}")

        saved_files.append({"filename": file.filename, "path": temp_path})

    PIPELINE_JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "stage": 0,
        "stage_name": "Ingest",
        "case_id": case_id,
        "logs": [],
        "result": None
    }

    if sync:
        await run_pipeline_job(job_id, saved_files, case_id)
        job = PIPELINE_JOBS[job_id]
        if job.get("status") == "completed" and job.get("result"):
            return {
                "job_id": job_id,
                "status": "completed",
                **job["result"]
            }
        return {
            "job_id": job_id,
            "status": job.get("status"),
            "error": job.get("logs", [{}])[-1].get("message", "Sync execution failed")
        }

    # Asynchronous execution
    asyncio.create_task(run_pipeline_job(job_id, saved_files, case_id))

    return {
        "job_id": job_id,
        "status": "queued",
        "stage": 0,
        "stage_name": "Ingest",
        "message": "Pipeline processing enqueued in background. Real-time updates pushed via WebSocket/Job API."
    }

@router.get("/pipeline/jobs/{job_id}")
def get_pipeline_job(job_id: str):
    job = PIPELINE_JOBS.get(job_id)
    if not job:
        return {"status": "not_found", "message": f"Job {job_id} not found"}
    return job

@router.websocket("/pipeline/ws/{job_id}")
async def pipeline_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in WEBSOCKET_CLIENTS:
        WEBSOCKET_CLIENTS[job_id] = []
    WEBSOCKET_CLIENTS[job_id].append(websocket)

    # Send current state immediately upon connection
    job = PIPELINE_JOBS.get(job_id)
    if job:
        await websocket.send_json({
            "job_id": job_id,
            "status": job["status"],
            "stage": job["stage"],
            "stage_name": job["stage_name"],
            "message": f"Connected to pipeline job {job_id}",
            "logs": job["logs"],
            "result": job["result"]
        })

    try:
        while True:
            # Keepalive ping/pong
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if job_id in WEBSOCKET_CLIENTS and websocket in WEBSOCKET_CLIENTS[job_id]:
            WEBSOCKET_CLIENTS[job_id].remove(websocket)
    except Exception:
        if job_id in WEBSOCKET_CLIENTS and websocket in WEBSOCKET_CLIENTS[job_id]:
            WEBSOCKET_CLIENTS[job_id].remove(websocket)

@router.get("/ingestion-audit")
def get_ingestion_audit():
    import json
    audit_path = os.path.join(os.path.dirname(__file__), "../../../data/ingestion_audit.json")
    try:
        with open(audit_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

@router.get("/filtered-edges")
def get_filtered_edges():
    import json
    path = os.path.join(os.path.dirname(__file__), "../../../data/filtered_edges.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
