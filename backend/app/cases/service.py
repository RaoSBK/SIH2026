# -*- coding: utf-8 -*-

from sqlalchemy.orm import Session
from backend.app.cases import repository
from backend.app.cases.schemas import CaseCreate
from backend.app.utils.exceptions import not_found, bad_request
from uuid import UUID

def create_case(db: Session, case_data: CaseCreate, user_id: UUID):
    existing = repository.get_case(db, case_data.case_id)
    if existing:
        raise bad_request(f"Case with id {case_data.case_id} already exists")
    
    case = repository.create_case(db, case_data, user_id)
    
    # Auto-assign the creator to the case
    repository.assign_user_to_case(db, case.case_id, user_id)
    return case

def get_cases(db: Session, user_id: UUID, role: str):
    is_admin = role in ("supervisor", "system_admin")
    return repository.get_cases_for_user(db, user_id, is_admin)

def get_case_detail(db: Session, case_id: str):
    case = repository.get_case(db, case_id)
    if not case:
        raise not_found("Case not found")
    return case

def assign_user(db: Session, case_id: str, user_id: UUID):
    case = repository.get_case(db, case_id)
    if not case:
        raise not_found("Case not found")
        
    if repository.is_user_assigned(db, user_id, case_id):
        raise bad_request("User already assigned to this case")
        
    return repository.assign_user_to_case(db, case_id, user_id)
