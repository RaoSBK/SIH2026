# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class CaseCreate(BaseModel):
    case_id: str = Field(..., description="Format: CASE-<number>")
    title: str
    description: Optional[str] = None

class CaseOut(BaseModel):
    case_id: str
    title: str
    description: Optional[str]
    status: str
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CaseAssign(BaseModel):
    user_id: UUID
