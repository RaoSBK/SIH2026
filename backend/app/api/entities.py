# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends
from backend.app.auth.rbac import get_current_user
from backend.app.users.models import User
from backend.app.entities import service
from backend.app.entities.schemas import EntityDetail

router = APIRouter()

@router.get("/{entity_id}", response_model=EntityDetail)
def get_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Returns full details and direct relationships for a single entity node from Neo4j.
    Role: Any authenticated user.
    """
    return service.get_entity_detail(entity_id)
