# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from backend.app.database.postgres import get_db
from backend.app.users.schemas import UserOut, UserUpdate
from backend.app.users import service as user_service
from backend.app.auth.rbac import require_role

router = APIRouter()

@router.get("", response_model=List[UserOut], dependencies=[Depends(require_role("system_admin", "supervisor"))])
def get_users(db: Session = Depends(get_db)):
    return user_service.list_users(db)

@router.patch("/{user_id}/role", response_model=UserOut, dependencies=[Depends(require_role("system_admin"))])
def update_role(user_id: UUID, role_update: UserUpdate, db: Session = Depends(get_db)):
    return user_service.update_user_role(db, user_id, role_update.role)
