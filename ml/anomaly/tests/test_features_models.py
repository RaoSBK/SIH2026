import pytest
import numpy as np

from ml.anomaly.features.graph_features import extract_graph_features
from ml.anomaly.features.transaction_features import extract_transaction_features
from ml.anomaly.features.communication_features import extract_communication_features
from ml.anomaly.models.isolation_forest import IsolationForestAnomalyModel
from ml.anomaly.models.scoring import build_feature_matrix, score_graph_anomalies

@pytest.fixture
def sample_graph():
    return {
        "nodes": [
            {"id": "node_a", "type": "PERSON"},
            {"id": "node_b", "type": "PERSON"},
            {"id": "node_c", "type": "PERSON"}
        ],
        "edges": [
            {"id": "e1", "source": "node_a", "target": "node_b", "type": "TRANSACTION", "amount": 10000.0},
            {"id": "e2", "source": "node_a", "target": "node_c", "type": "CALL", "duration": 180.0},
            {"id": "e3", "source": "node_b", "target": "node_c", "type": "TRANSACTION", "amount": 5000.0}
        ]
    }

def test_graph_features(sample_graph):
    feats = extract_graph_features(sample_graph)
    assert "node_a" in feats
    assert feats["node_a"]["out_degree"] == 2.0
    assert feats["node_a"]["in_degree"] == 0.0

def test_transaction_features(sample_graph):
    feats = extract_transaction_features(sample_graph)
    assert "node_a" in feats
    assert feats["node_a"]["tx_out_count"] == 1.0
    assert feats["node_a"]["tx_total_volume"] == 10000.0

def test_communication_features(sample_graph):
    feats = extract_communication_features(sample_graph)
    assert "node_a" in feats
    assert feats["node_a"]["call_out_count"] == 1.0
    assert feats["node_a"]["call_total_duration"] == 180.0

def test_isolation_forest_model():
    X = np.random.randn(20, 5)
    # Add an extreme outlier
    X[0] = [100.0, 100.0, 100.0, 100.0, 100.0]
    
    model = IsolationForestAnomalyModel(n_estimators=50, contamination=0.1, random_state=42)
    preds, confs = model.fit_predict_confidence(X)
    
    assert len(preds) == 20
    assert len(confs) == 20
    assert preds[0] == -1
    assert confs[0] >= 0.70

def test_scoring_pipeline(sample_graph):
    entity_ids, X, feature_names, evidence_map = build_feature_matrix(sample_graph)
    assert len(entity_ids) == 3
    assert X.shape == (3, 16)
    
    alerts = score_graph_anomalies(sample_graph)
    assert isinstance(alerts, list)
