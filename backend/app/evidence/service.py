# -*- coding: utf-8 -*-

from sqlalchemy.orm import Session
from uuid import UUID
from backend.app.evidence.models import EvidenceFile
from backend.app.evidence import storage
from backend.app.utils.exceptions import bad_request, not_found

def upload_evidence(db: Session, file_bytes: bytes, evidence_id: str, case_id: str, file_name: str, user_id: UUID) -> EvidenceFile:
    existing = db.query(EvidenceFile).filter(EvidenceFile.evidence_id == evidence_id).first()
    if existing:
        raise bad_request(f"Evidence with id {evidence_id} already exists")

    storage_path = storage.save_file(file_bytes, case_id, file_name)

    # TODO(blockchain): once blockchain/hashing/sha256.py is implemented, call it
    # here and store the result in EvidenceFile.sha256. Left as None until then.
    sha256_hash = None

    evidence = EvidenceFile(
        evidence_id=evidence_id,
        case_id=case_id,
        file_name=file_name,
        storage_path=storage_path,
        sha256=sha256_hash,
        uploaded_by=user_id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence

def list_evidence_for_case(db: Session, case_id: str):
    return db.query(EvidenceFile).filter(EvidenceFile.case_id == case_id).all()

def get_evidence_file_bytes(db: Session, evidence_id: str):
    evidence = db.query(EvidenceFile).filter(EvidenceFile.evidence_id == evidence_id).first()
    if not evidence:
        raise not_found("Evidence file not found")
        
    return storage.get_file(evidence.storage_path)
