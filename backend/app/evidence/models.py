# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.postgres import Base

class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    evidence_id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
