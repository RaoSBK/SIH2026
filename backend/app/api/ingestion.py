import os
import shutil
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..ingestion.service import process_file
from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine
from .anomaly import save_anomaly_alerts, load_stored_anomaly_alerts
from .evidence import integrity_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Ingestion"])

@router.post("/process-evidence")
async def process_evidence(
    files: List[UploadFile] = File(...),
    case_id: str = Form("CASE-102")
):
    """
    Universal multi-format document ingestion pipeline (PDF, DOCX, CSV, JSON, TXT).
    Performs OCR cleaning, spaCy & regex NER, Entity Resolution, graph database insertion,
    SHA-256 evidence logging, and Isolation Forest ML anomaly scoring.
    """
    logger.info(f"Received {len(files)} files for processing via ingestion layer. Case: {case_id}")

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

            # Cryptographically log evidence SHA-256 hash & update case Merkle Root
            try:
                integrity_client.register_evidence(file_name=file.filename, case_id=case_id, file_path=temp_path)
            except Exception as ex:
                logger.warning(f"Failed to log evidence hash for {file.filename}: {ex}")

            # Run synchronous (blocking) NLP work off the event loop thread
            result = await asyncio.to_thread(
                process_file,
                temp_path,
                None,           # file_type: auto-detect from extension
                "investigator_upload",
                case_id,        # Propagate case_id
            )

            statuses.append({
                "filename": file.filename,
                "status": result["status"],
                "message": result.get("message"),
                "reason": result.get("reason"),
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

    # Anomaly Detection: Stage 1 (Rule Engine) & Stage 2 (ML Isolation Forest)
    graph_payload = {"nodes": list(global_nodes.values()), "edges": unique_links}
    try:
        rule_alerts = run_rule_engine(graph_payload)
        ml_alerts = run_ml_engine(graph_payload)
        all_alerts = rule_alerts + ml_alerts

        if all_alerts:
            existing = load_stored_anomaly_alerts()
            existing_ids = {a.get("alert_id") for a in existing if a.get("alert_id")}
            new_unique = [a for a in all_alerts if a.get("alert_id") not in existing_ids]
            save_anomaly_alerts((new_unique + existing)[:200])

        for alert in all_alerts:
            ent_id = alert.get("entity_id")
            if ent_id in global_nodes:
                node = global_nodes[ent_id]
                node["flagged"] = True
                node.setdefault("anomaly_reasons", []).append(alert.get("reason"))
                conf = alert.get("confidence", 0.7)
                if conf >= 0.8:
                    node["status"] = "REVIEW_REQUIRED"
                    node["risk_color"] = "red"
                elif node.get("risk_color") != "red":
                    node["status"] = "REVIEW_REQUIRED"
                    node["risk_color"] = "orange"
    except Exception as e:
        logger.warning(f"Anomaly detection engine execution warning: {e}")

    return {
        "nodes": list(global_nodes.values()),
        "links": unique_links,
        "statuses": statuses,
        "ingestion_statuses": statuses,
        "needs_review": all_needs_review
    }
