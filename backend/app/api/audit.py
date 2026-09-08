import os
import json
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Audit & Provenance"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
AUDIT_LOG_PATH = os.path.join(DATA_DIR, "ingestion_audit.json")
FILTERED_EDGES_PATH = os.path.join(DATA_DIR, "filtered_edges.json")

@router.get("/ingestion-audit")
def get_ingestion_audit():
    """Returns the ingestion audit log for data history and provenance UI screens."""
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

@router.get("/filtered-edges")
def get_filtered_edges():
    """
    Returns the full audit trail of removed edges (self-loops, phone conflicts).
    """
    try:
        with open(FILTERED_EDGES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
