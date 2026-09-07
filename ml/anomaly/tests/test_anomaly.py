import pytest
from ml.anomaly.anomaly_ml import run_ml_engine
from ml.anomaly.anomaly_rules import run_rule_engine

@pytest.fixture
def graph_with_anomalies():
    return {
        "nodes": [
            {"id": "person_1", "type": "PERSON"},
            {"id": "person_2", "type": "PERSON"},
            {"id": "person_3", "type": "PERSON"}
        ],
        "edges": [
            {"id": "e1", "source": "person_1", "target": "person_2", "type": "TRANSACTION", "amount": 100000.0, "timestamp": "2024-01-01T10:00:00"},
            {"id": "e2", "source": "person_1", "target": "person_2", "type": "TRANSACTION", "amount": 200000.0, "timestamp": "2024-01-02T10:00:00"},
            {"id": "e3", "source": "person_1", "target": "person_3", "type": "CALL", "duration": 500.0, "timestamp": "2024-01-03T10:00:00"}
        ]
    }

def test_ml_anomaly_engine(graph_with_anomalies):
    alerts = run_ml_engine(graph_with_anomalies)
    assert isinstance(alerts, list)

def test_rule_anomaly_engine(graph_with_anomalies):
    alerts = run_rule_engine(graph_with_anomalies)
    assert isinstance(alerts, list)
