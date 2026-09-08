import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.postgres import get_db
from backend.app.auth.rbac import get_current_user
from backend.app.users.models import User
from backend.app.evidence import service
from backend.app.evidence.schemas import EvidenceOut
from blockchain.client.fabric_client import BlockchainIntegrityClient

logger = logging.getLogger(__name__)
router = APIRouter()
integrity_client = BlockchainIntegrityClient()

class EvidenceVerifyPayload(BaseModel):
    file_name: str
    file_hash: str
    case_id: Optional[str] = "CASE-102"

# Local dependency to check case access dynamically for form data
def check_case_access(case_id: str = Form(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.app.cases.repository import is_user_assigned
    from backend.app.utils.exceptions import forbidden
    if user.role in ("supervisor", "system_admin"):
        return case_id
    if not is_user_assigned(db, user.id, case_id):
        raise forbidden(f"Not assigned to case {case_id}")
    return case_id

def check_case_access_path(case_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.app.cases.repository import is_user_assigned
    from backend.app.utils.exceptions import forbidden
    if user.role in ("supervisor", "system_admin"):
        return case_id
    if not is_user_assigned(db, user.id, case_id):
        raise forbidden(f"Not assigned to case {case_id}")
    return case_id

@router.post("", response_model=EvidenceOut)
async def upload_evidence(
    evidence_id: str = Form(...),
    case_id: str = Depends(check_case_access),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_bytes = await file.read()
    return service.upload_evidence(
        db=db,
        file_bytes=file_bytes,
        evidence_id=evidence_id,
        case_id=case_id,
        file_name=file.filename,
        user_id=current_user.id
    )

@router.get("/{case_id}", response_model=List[EvidenceOut], dependencies=[Depends(check_case_access_path)])
def list_evidence(case_id: str, db: Session = Depends(get_db)):
    return service.list_evidence_for_case(db, case_id)

@router.get("/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_bytes = service.get_evidence_file_bytes(db, evidence_id)
    return Response(content=file_bytes, media_type="application/octet-stream")

@router.post("/verify")
def verify_evidence_hash(payload: EvidenceVerifyPayload):
    """
    Verifies an evidence document's SHA-256 hash against the tamper-evident ledger.
    """
    result = integrity_client.verify_file(payload.file_name, payload.file_hash, payload.case_id)
    return result

@router.get("/{case_id}/integrity")
def get_case_integrity_endpoint(case_id: str):
    """
    Retrieves the Merkle Root Hash and evidence checksum tree for a specific case.
    """
    result = integrity_client.get_case_integrity(case_id)
    return result

@router.get("/ledger")
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
