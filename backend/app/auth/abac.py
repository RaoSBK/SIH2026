# -*- coding: utf-8 -*-

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.auth.rbac import get_current_user
from backend.app.database.postgres import get_db
from backend.app.users.models import User

def require_case_access(case_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # We import repository locally to prevent circular imports before it's created in Phase 6
    from backend.app.cases.repository import is_user_assigned
    
    # supervisor/system_admin bypass; everyone else must have a CaseAssignment row
    if user.role in ("supervisor", "system_admin"):
        return user
        
    assigned = is_user_assigned(db, user.id, case_id)
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Not assigned to case {case_id}"
        )
        
    return user
