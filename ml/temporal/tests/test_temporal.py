import pytest
from datetime import datetime, timedelta
from ml.temporal.activity_patterns import detect_burst_activity, detect_off_hours_activity
from ml.temporal.network_changes import track_network_evolution, detect_new_connections
from ml.temporal.feature_builder import build_temporal_features

@pytest.fixture
def sample_temporal_graph():
    now = datetime.now()
    return {
        "nodes": [
            {"id": "node_1", "type": "PERSON"},
            {"id": "node_2", "type": "PERSON"},
            {"id": "node_3", "type": "PERSON"}
        ],
        "edges": [
            {"id": "e1", "source": "node_1", "target": "node_2", "type": "CALL", "timestamp": (now - timedelta(days=20)).isoformat()},
            {"id": "e2", "source": "node_1", "target": "node_2", "type": "CALL", "timestamp": (now - timedelta(days=19)).isoformat()},
            # Off-hours call at 02:00
            {"id": "e3", "source": "node_1", "target": "node_3", "type": "CALL", "timestamp": now.replace(hour=2, minute=15).isoformat()},
            # Recent burst
            {"id": "e4", "source": "node_1", "target": "node_2", "type": "CALL", "timestamp": (now - timedelta(days=1)).isoformat()},
            {"id": "e5", "source": "node_1", "target": "node_2", "type": "CALL", "timestamp": (now - timedelta(days=1, hours=2)).isoformat()},
            {"id": "e6", "source": "node_1", "target": "node_3", "type": "CALL", "timestamp": (now - timedelta(hours=3)).isoformat()}
        ]
    }

def test_detect_off_hours_activity(sample_temporal_graph):
    alerts = detect_off_hours_activity(sample_temporal_graph)
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    assert any(a["hour"] == 2 for a in alerts)

def test_track_network_evolution(sample_temporal_graph):
    slices = track_network_evolution(sample_temporal_graph, num_slices=2)
    assert len(slices) == 2
    assert "slice_index" in slices[0]

def test_detect_new_connections(sample_temporal_graph):
    new_conns = detect_new_connections(sample_temporal_graph)
    assert isinstance(new_conns, list)

def test_build_temporal_features(sample_temporal_graph):
    feats = build_temporal_features(sample_temporal_graph)
    assert "node_1" in feats
    assert "burst_score" in feats["node_1"]
    assert "off_hours_ratio" in feats["node_1"]
    assert feats["node_1"]["recent_velocity"] > 0
