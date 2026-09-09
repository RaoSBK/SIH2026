import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_evidence_ledger_endpoint():
    response = client.get("/api/evidence/ledger")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "records" in data

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
