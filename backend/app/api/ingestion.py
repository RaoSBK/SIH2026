# -*- coding: utf-8 -*-

from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import List
from sqlalchemy.orm import Session
import os
import shutil
import asyncio
import logging

from backend.app.auth.rbac import get_current_user
from backend.app.users.models import User
from backend.app.database.postgres import get_db
from backend.app.ingestion.service import process_file
from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-evidence")
async def process_evidence(
    files: List[UploadFile] = File(...),
    case_id: str = Form("CASE-102"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Received {len(files)} files for processing via ingestion layer. Case: {case_id}")

    # Auto-create case if it doesn't exist, to prevent ABAC failures during graph retrieval
    from backend.app.cases.repository import get_case
    from backend.app.cases.service import create_case
    from backend.app.cases.schemas import CaseCreate

    existing_case = get_case(db, case_id)
    if not existing_case:
        new_case_data = CaseCreate(case_id=case_id, title=f"Auto-generated Case {case_id}", description="Created during ingestion")
        create_case(db, new_case_data, current_user.id)


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

            result = await asyncio.to_thread(
                process_file,
                temp_path,
                None,
                "investigator_upload",
                case_id,
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

    # Node-specific phone attribute propagation
    for n_id, node in global_nodes.items():
        if node.get("type") == "PHONE" or node.get("type") == "Phone":
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

    # Distinct Evidence Scoring & Trail compilation
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

    # Flag repeatedly-implicated entities
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

    graph_payload = {"nodes": list(global_nodes.values()), "edges": unique_links}
    try:
        rule_alerts = run_rule_engine(graph_payload)
        ml_alerts = run_ml_engine(graph_payload)
        all_alerts = rule_alerts + ml_alerts
        
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
        logger.warning(f"Anomaly detection engine execution warning: {e}")

    # Fallback connectivity baseline for nodes with no other flags
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

    return {
        "nodes": list(global_nodes.values()),
        "links": unique_links,
        "ingestion_statuses": statuses,
        "needs_review": all_needs_review
    }

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
