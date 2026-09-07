import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_case_analytics_endpoint():
    response = client.get("/api/cases/CASE-102/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-102"
    assert "top_influencers" in data

def test_run_custom_analytics_endpoint():
    payload = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [{"source": "a", "target": "b"}]
    }
    response = client.post("/api/analytics/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_shortest_path_endpoint():
    response = client.get("/api/analytics/shortest-path?case_id=CASE-102&source=n1&target=n2")
    assert response.status_code == 200
