# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class EvidenceCreate(BaseModel):
    evidence_id: str = Field(..., description="Format: EV-<number>")
    case_id: str
    file_name: str

class EvidenceOut(BaseModel):
    evidence_id: str
    case_id: str
    file_name: str
    sha256: Optional[str]
    uploaded_by: UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True
