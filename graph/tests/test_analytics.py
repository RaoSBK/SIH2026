import pytest
from graph.analytics.pagerank import compute_pagerank
from graph.analytics.betweenness import compute_betweenness
from graph.analytics.communities import detect_communities
from graph.analytics.degree import compute_degree_centrality
from graph.analytics.paths import find_shortest_path
from graph.services.analytics_service import GraphAnalyticsService

@pytest.fixture
def sample_graph():
    return {
        "nodes": [
            {"id": "n1", "type": "PERSON"},
            {"id": "n2", "type": "PERSON"},
            {"id": "n3", "type": "PERSON"},
            {"id": "n4", "type": "PERSON"}
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "type": "TRANSACTION"},
            {"id": "e2", "source": "n2", "target": "n3", "type": "CALL"},
            {"id": "e3", "source": "n3", "target": "n4", "type": "TRANSACTION"}
        ]
    }

def test_pagerank(sample_graph):
    pr = compute_pagerank(sample_graph)
    assert len(pr) == 4
    assert "n1" in pr

def test_betweenness(sample_graph):
    bw = compute_betweenness(sample_graph)
    assert len(bw) == 4
    assert bw["n2"] > bw["n1"]

def test_communities(sample_graph):
    comm_res = detect_communities(sample_graph)
    assert "communities" in comm_res
    assert "node_communities" in comm_res

def test_degree_centrality(sample_graph):
    deg = compute_degree_centrality(sample_graph)
    assert len(deg) == 4

def test_shortest_path(sample_graph):
    path_res = find_shortest_path(sample_graph, "n1", "n4")
    assert path_res["found"] is True
    assert path_res["distance"] == 3
    assert path_res["path"] == ["n1", "n2", "n3", "n4"]

def test_analytics_service(sample_graph):
    res = GraphAnalyticsService.run_full_analytics(sample_graph)
    assert res["nodes_count"] == 4
    assert len(res["top_influencers"]) > 0
