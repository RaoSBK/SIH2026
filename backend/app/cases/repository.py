# -*- coding: utf-8 -*-

from sqlalchemy.orm import Session
from backend.app.cases.models import Case, CaseAssignment
from backend.app.cases.schemas import CaseCreate
from uuid import UUID
from datetime import datetime

def create_case(db: Session, case_data: CaseCreate, user_id: UUID) -> Case:
    db_case = Case(
        case_id=case_data.case_id,
        title=case_data.title,
        description=case_data.description,
        created_by=user_id,
        status="open"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

def get_case(db: Session, case_id: str) -> Case:
    return db.query(Case).filter(Case.case_id == case_id).first()

def get_cases_for_user(db: Session, user_id: UUID, is_admin: bool = False):
    if is_admin:
        return db.query(Case).all()
    
    assigned_case_ids = db.query(CaseAssignment.case_id).filter(CaseAssignment.user_id == user_id).subquery()
    return db.query(Case).filter(Case.case_id.in_(assigned_case_ids)).all()

def assign_user_to_case(db: Session, case_id: str, user_id: UUID) -> CaseAssignment:
    assignment = CaseAssignment(case_id=case_id, user_id=user_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def is_user_assigned(db: Session, user_id: UUID, case_id: str) -> bool:
    count = db.query(CaseAssignment).filter(
        CaseAssignment.user_id == user_id,
        CaseAssignment.case_id == case_id
    ).count()
    return count > 0
