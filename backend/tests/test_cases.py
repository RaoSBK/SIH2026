# -*- coding: utf-8 -*-

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from backend.app.cases.models import Case
from backend.app.cases.schemas import CaseCreate
from backend.app.cases import service
from backend.app.users.models import User

def test_case_crud(db_session: Session):
    # Create mock user
    user_id = uuid4()
    user = User(id=user_id, username="testuser_cases", hashed_password="pw", role="investigator")
    db_session.add(user)
    db_session.commit()
    
    # Create Case
    case_in = CaseCreate(case_id="CASE-101", title="Test Case", description="Test Description")
    case = service.create_case(db_session, case_in, user_id)
    
    assert case.case_id == "CASE-101"
    assert case.title == "Test Case"
    assert case.created_by == user_id
    
    # Read Case
    fetched = service.get_case_detail(db_session, "CASE-101")
    assert fetched.title == "Test Case"
    
    # Check assignments
    cases_for_user = service.get_cases(db_session, user_id, "investigator")
    assert len(cases_for_user) == 1
    assert cases_for_user[0].case_id == "CASE-101"
    
    # Assign another user
    other_user_id = uuid4()
    service.assign_user(db_session, "CASE-101", other_user_id)
    cases_for_other = service.get_cases(db_session, other_user_id, "investigator")
    assert len(cases_for_other) == 1
