import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Anomaly Detection"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
ANOMALY_ALERTS_PATH = os.path.join(DATA_DIR, "anomaly_alerts.json")


class GraphEdgePayload(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    type: Optional[str] = "CONNECTED_TO"
    amount: Optional[float] = None
    duration: Optional[float] = None
    timestamp: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class GraphNodePayload(BaseModel):
    id: str
    name: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = "ENTITY"
    status: Optional[str] = "VERIFIED"


class GraphDetectPayload(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


def save_anomaly_alerts(alerts: List[Dict[str, Any]]):
    """Persists anomaly alerts to data/anomaly_alerts.json."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ANOMALY_ALERTS_PATH, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write anomaly alerts log: {e}")


def load_stored_anomaly_alerts() -> List[Dict[str, Any]]:
    """Loads anomaly alerts from data/anomaly_alerts.json."""
    if not os.path.exists(ANOMALY_ALERTS_PATH):
        return []
    try:
        with open(ANOMALY_ALERTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read anomaly alerts log: {e}")
        return []


@router.get("/anomalies")
def get_all_anomalies():
    """
    Returns all persisted ML and rule-based anomaly alerts.
    """
    alerts = load_stored_anomaly_alerts()
    return {
        "status": "success",
        "total": len(alerts),
        "alerts": alerts
    }


@router.post("/anomalies/detect")
def detect_anomalies(payload: GraphDetectPayload):
    """
    Executes Stage 1 (Rule Engine) and Stage 2 (Isolation Forest ML Engine)
    anomaly detection on an incoming graph payload.
    """
    graph_data = {
        "nodes": payload.nodes,
        "edges": payload.edges
    }

    try:
        rule_alerts = run_rule_engine(graph_data)
        ml_alerts = run_ml_engine(graph_data)
        all_alerts = rule_alerts + ml_alerts

        # Merge with stored alerts
        existing = load_stored_anomaly_alerts()
        # Keep recent unique alerts by alert_id
        existing_ids = {a.get("alert_id") for a in existing if a.get("alert_id")}
        new_unique = [a for a in all_alerts if a.get("alert_id") not in existing_ids]
        combined = new_unique + existing

        save_anomaly_alerts(combined[:200])  # Cap at recent 200 alerts

        return {
            "status": "success",
            "rule_alerts_count": len(rule_alerts),
            "ml_alerts_count": len(ml_alerts),
            "total_alerts": len(all_alerts),
            "alerts": all_alerts
        }
    except Exception as e:
        logger.error(f"Error executing anomaly detection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.get("/cases/{case_id}/anomalies")
def get_case_anomalies(case_id: str):
    """
    Computes real-time rule and ML anomaly scores for a specific case's graph.
    """
    from ..main import get_case_graph

    graph_res = get_case_graph(case_id)
    nodes = graph_res.get("nodes", [])
    edges = graph_res.get("edges", [])

    if not nodes:
        return {
            "case_id": case_id,
            "total_alerts": 0,
            "alerts": []
        }

    graph_payload = {"nodes": nodes, "edges": edges}
    try:
        rule_alerts = run_rule_engine(graph_payload)
        ml_alerts = run_ml_engine(graph_payload)
        alerts = rule_alerts + ml_alerts

        return {
            "case_id": case_id,
            "rule_alerts_count": len(rule_alerts),
            "ml_alerts_count": len(ml_alerts),
            "total_alerts": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error computing case anomalies for {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
