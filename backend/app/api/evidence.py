# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from backend.app.database.postgres import get_db
from backend.app.auth.rbac import get_current_user
from backend.app.users.models import User
from backend.app.evidence import service
from backend.app.evidence.schemas import EvidenceOut

router = APIRouter()

# Local dependency to check case access dynamically for form data
def check_case_access(case_id: str = Form(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

# Path dependency for case access
def check_case_access_path(case_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.app.cases.repository import is_user_assigned
    from backend.app.utils.exceptions import forbidden
    if user.role in ("supervisor", "system_admin"):
        return case_id
    if not is_user_assigned(db, user.id, case_id):
        raise forbidden(f"Not assigned to case {case_id}")
    return case_id

@router.get("/{case_id}", response_model=List[EvidenceOut], dependencies=[Depends(check_case_access_path)])
def list_evidence(case_id: str, db: Session = Depends(get_db)):
    return service.list_evidence_for_case(db, case_id)

@router.get("/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Note: A real app would check if current_user has access to the evidence_id's case
    file_bytes = service.get_evidence_file_bytes(db, evidence_id)
    return Response(content=file_bytes, media_type="application/octet-stream")
