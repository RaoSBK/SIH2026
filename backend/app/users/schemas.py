# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str

class UserOut(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    role: str
