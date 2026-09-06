import os
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_get_anomalies_endpoint():
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "alerts" in data
    assert isinstance(data["alerts"], list)

def test_detect_anomalies_endpoint():
    payload = {
        "nodes": [
            {"id": "person_1", "type": "PERSON", "name": "Suspect A"},
            {"id": "person_2", "type": "PERSON", "name": "Suspect B"},
            {"id": "person_3", "type": "PERSON", "name": "Suspect C"}
        ],
        "edges": [
            {"id": "e1", "source": "person_1", "target": "person_2", "type": "TRANSACTION", "amount": 50000.0, "timestamp": "2024-01-15T10:00:00"},
            {"id": "e2", "source": "person_1", "target": "person_2", "type": "TRANSACTION", "amount": 75000.0, "timestamp": "2024-01-16T10:00:00"},
            {"id": "e3", "source": "person_1", "target": "person_3", "type": "CALL", "duration": 300, "timestamp": "2024-01-16T11:00:00"}
        ]
    }
    response = client.post("/api/anomalies/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "total_alerts" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)

def test_get_case_anomalies_endpoint():
    response = client.get("/api/cases/CASE-102/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-102"
    assert "alerts" in data
