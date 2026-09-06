from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
import asyncio
import json

from .ingestion.service import process_file
from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

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

@app.get("/api/cases/{case_id}/graph")
def get_case_graph(case_id: str):
    """
    Reads nodes and edges for a given case directly from Neo4j.
    All IDs are keyed on the node's own custom `id` property (e.g. person:a7ca11a0),
    never the Neo4j internal element_id — this guarantees edge source/target
    always matches a node id on the frontend canvas.
    """
    from .database.neo4j import driver as neo4j_driver
    try:
        with neo4j_driver.session() as session:
            nodes_result = session.run(
                "MATCH (n)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id}) "
                "RETURN DISTINCT n.id AS id, n.value AS value, "
                "       labels(n)[0] AS type, n.confidence AS confidence, "
                "       n.status AS status, n.risk_color AS risk_color, "
                "       n.historical_firs AS historical_firs",
                case_id=case_id
            )
            nodes = [dict(r) for r in nodes_result]

            edges_result = session.run(
                "MATCH (a)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id}) "
                "MATCH (a)-[r]->(b) WHERE type(r) <> 'EXTRACTED_FROM' "
                "RETURN a.id AS source, b.id AS target, type(r) AS type, "
                "       r.confidence AS confidence, r.status AS status, r.evidence AS evidence",
                case_id=case_id
            )
            edges = [dict(r) for r in edges_result]

        # Drop edges whose endpoints don't exist in the node set
        valid_ids = {n["id"] for n in nodes}
        dropped = [e for e in edges if e["source"] not in valid_ids or e["target"] not in valid_ids]
        if dropped:
            logger.warning(f"[get_case_graph] Dropped {len(dropped)}/{len(edges)} edges — "
                           f"source or target id not in node set:")
            for e in dropped[:10]:
                logger.warning(f"  {e['source']} --{e['type']}--> {e['target']}")
        edges = [e for e in edges if e["source"] in valid_ids and e["target"] in valid_ids]

        return {"nodes": nodes, "edges": edges, "case_id": case_id}
    except Exception as e:
        logger.error(f"[get_case_graph] Failed for case {case_id}: {e}")
        return {"nodes": [], "edges": [], "case_id": case_id, "error": str(e)}

@app.post("/api/process-evidence")
async def process_evidence(
    files: List[UploadFile] = File(...),
    case_id: str = Form("CASE-102")
):
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

            # Run synchronous (blocking) NLP work off the event loop thread
            result = await asyncio.to_thread(
                process_file,
                temp_path,
                None,           # file_type: auto-detect from extension
                "investigator_upload",
                case_id,        # Propagate case_id so resolver can use it as a corroborating signal
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

    # Deduplicate links
    unique_links = []
    seen = set()
    for l in global_links:
        h = f"{l['source']}-{l['target']}-{l['type']}"
        if h not in seen:
            seen.add(h)
            unique_links.append(l)

    # Anomaly Detection: Stage 1 (Rule Engine) & Stage 2 (ML Isolation Forest)
    graph_payload = {"nodes": list(global_nodes.values()), "edges": unique_links}
    try:
        rule_alerts = run_rule_engine(graph_payload)
        ml_alerts = run_ml_engine(graph_payload)
        all_alerts = rule_alerts + ml_alerts
        
        for alert in all_alerts:
            ent_id = alert.get("entity_id")
            if ent_id in global_nodes:
                node = global_nodes[ent_id]
                node.setdefault("anomaly_reasons", []).append(alert.get("reason"))
                conf = alert.get("confidence", 0.7)
                if conf >= 0.8:
                    node["status"] = "REVIEW_REQUIRED"
                    node["risk_color"] = "red"
                    node["historical_firs"] = 1
                elif node.get("risk_color") != "red":
                    node["status"] = "REVIEW_REQUIRED"
                    node["risk_color"] = "orange"
    except Exception as e:
        logger.warning(f"Anomaly detection engine execution warning: {e}")

    # Connectivity baseline fallback for unflagged nodes
    degrees = {n_id: 0 for n_id in global_nodes}
    for l in unique_links:
        if l['source'] in degrees: degrees[l['source']] += 1
        if l['target'] in degrees: degrees[l['target']] += 1
        
    for n_id, n in global_nodes.items():
        if "risk_color" not in n or n["risk_color"] == "none":
            if degrees[n_id] >= 5:
                n['status'] = 'REVIEW_REQUIRED'
                n['risk_color'] = 'red'
                n['historical_firs'] = 1
            elif degrees[n_id] >= 3:
                n['status'] = 'REVIEW_REQUIRED'
                n['risk_color'] = 'orange'
            else:
                n['risk_color'] = 'none'

    return {
        "nodes": list(global_nodes.values()),
        "links": unique_links,
        "statuses": statuses,
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

from pydantic import BaseModel

class ReviewAction(BaseModel):
    action: str  # 'merge', 'reject', 'skip'

@app.post("/api/review-queue/{review_id}/resolve")
def resolve_review_item(review_id: str, payload: ReviewAction):
    """
    Resolves a pending review item.
    In a full production environment, 'merge' would execute a graph refactoring algorithm
    to combine the nodes and edges in Neo4j. For now, we clear the item from the queue
    and log the investigator's decision.
    """
    registry_path = os.path.join(os.path.dirname(__file__), "../../data/entity_registry.json")
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        needs_review = data.get("needs_review", [])
        
        # We need a stable ID for review items. Since they don't have one intrinsically yet,
        # we match on the stringified review_id (could be passed from frontend as an index or hash).
        # For this prototype, we'll assume review_id matches the candidate ID or a hash.
        # But to be safe, we'll just filter out any item whose candidate/names matches the review_id string loosely.
        
        updated_queue = []
        resolved_item = None
        
        for item in needs_review:
            # Create a simple unique-ish identifier for the item
            item_id = ""
            if item.get("type") == "PHONE_CONFLICT":
                item_id = "-".join(item.get("names", []))
            else:
                c = item.get("candidate", {}).get("id", "")
                p = item.get("possible_match", {}).get("id", "")
                item_id = f"{c}-{p}"
                
            # If the frontend passes this item_id, we resolve it
            if item_id == review_id:
                resolved_item = item
            else:
                updated_queue.append(item)
                
        data["needs_review"] = updated_queue
        
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if payload.action == "merge" and resolved_item and resolved_item.get("type") == "PERSON_NAME_AMBIGUITY":
            try:
                from .database.neo4j import merge_nodes_in_neo4j
                source_id = resolved_item.get("candidate", {}).get("id")
                target_id = resolved_item.get("possible_match", {}).get("id")
                if source_id and target_id:
                    merge_nodes_in_neo4j(source_id, target_id)
            except Exception as ex:
                logger.warning(f"Neo4j merge notice: {ex}")
            
        logger.info(f"Resolved review item {review_id} with action: {payload.action}")
        return {"status": "success", "action": payload.action, "remaining": len(updated_queue)}
        
    except Exception as e:
        logger.error(f"Failed to resolve review item: {e}")
        return {"status": "error", "message": str(e)}
