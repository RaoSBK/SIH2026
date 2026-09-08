import os
import pytest

from backend.app.database.postgres import (
    init_db,
    save_case_db,
    get_cases_db,
    save_audit_log_db,
    get_audit_logs_db,
    SessionLocal
)

def test_database_initialization():
    init_db()
    session = SessionLocal()
    assert session is not None
    session.close()

def test_case_db_crud():
    res1 = save_case_db("CASE-888", "Test case description")
    assert res1["status"] in ("created", "exists")

    cases = get_cases_db()
    assert isinstance(cases, list)

def test_audit_log_db_crud():
    res1 = save_audit_log_db(
        file_name="FIR_test.txt",
        source_label="investigator_upload",
        case_id="CASE-888",
        status="success",
        message="Extracted 3 entities.",
        entities_count=3,
        new_nodes=2
    )
    assert res1["status"] == "success"

    logs = get_audit_logs_db()
    assert isinstance(logs, list)
