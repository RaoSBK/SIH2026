import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

from uuid import uuid4
from backend.app.auth.rbac import get_current_user
from backend.app.database.postgres import get_db, Base
from backend.app.users.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

mock_user = User(id=uuid4(), username="testuser", role="supervisor")
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_get_evidence_ledger_endpoint():
    response = client.get("/api/evidence/ledger")
    assert response.status_code == 200
    data = response.json()
    assert data is not None

def test_get_case_integrity_endpoint():
    response = client.get("/api/evidence/CASE-102/integrity")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-102"
    assert "merkle_root" in data

def test_verify_evidence_hash_endpoint():
    payload = {
        "file_name": "test_file.txt",
        "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "case_id": "CASE-102"
    }
    response = client.post("/api/evidence/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "verified" in data
