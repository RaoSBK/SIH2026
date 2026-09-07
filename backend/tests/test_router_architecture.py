import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_cases_router_endpoints():
    res1 = client.get("/api/cases")
    assert res1.status_code == 200
    assert "cases" in res1.json()

    res2 = client.post("/api/cases", json={"case_id": "CASE-999"})
    assert res2.status_code == 200
    assert res2.json()["case_id"] == "CASE-999"

    res3 = client.get("/api/cases/CASE-102/graph")
    assert res3.status_code == 200

def test_entities_router_endpoints():
    res1 = client.get("/api/needs-review")
    assert res1.status_code == 200

    res2 = client.get("/api/review-queue")
    assert res2.status_code == 200
    assert "pending_review" in res2.json()

def test_audit_router_endpoints():
    res1 = client.get("/api/ingestion-audit")
    assert res1.status_code == 200

    res2 = client.get("/api/filtered-edges")
    assert res2.status_code == 200

def test_graph_router_endpoints():
    res1 = client.get("/api/graph/schema")
    assert res1.status_code == 200
