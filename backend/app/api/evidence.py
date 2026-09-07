import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from blockchain.client.fabric_client import BlockchainIntegrityClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Evidence Integrity"])
integrity_client = BlockchainIntegrityClient()

class EvidenceVerifyPayload(BaseModel):
    file_name: str
    file_hash: str
    case_id: Optional[str] = "CASE-102"

@router.post("/evidence/verify")
def verify_evidence_hash(payload: EvidenceVerifyPayload):
    """
    Verifies an evidence document's SHA-256 hash against the tamper-evident ledger.
    """
    result = integrity_client.verify_file(payload.file_name, payload.file_hash, payload.case_id)
    return result

@router.get("/cases/{case_id}/integrity")
def get_case_integrity_endpoint(case_id: str):
    """
    Retrieves the Merkle Root Hash and evidence checksum tree for a specific case.
    """
    result = integrity_client.get_case_integrity(case_id)
    return result

@router.get("/evidence/ledger")
def get_evidence_ledger():
    """
    Returns the complete evidence ledger containing SHA-256 digests and Merkle Roots.
    """
    ledger = integrity_client.load_ledger()
    return {
        "status": "success",
        "total_records": len(ledger.get("records", [])),
        "records": ledger.get("records", []),
        "cases": ledger.get("cases", {})
    }
