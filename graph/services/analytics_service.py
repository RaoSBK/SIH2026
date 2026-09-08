from typing import Dict, List, Any
from ..analytics.pagerank import compute_pagerank
from ..analytics.betweenness import compute_betweenness
from ..analytics.communities import detect_communities
from ..analytics.degree import compute_degree_centrality
from ..analytics.paths import find_shortest_path

class GraphAnalyticsService:
    """
    Unified service for running full network graph analytics.
    """
    @staticmethod
    def run_full_analytics(graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes PageRank, Betweenness Centrality, Degree Centrality,
        and Community Detection on the given graph_data.
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if not nodes:
            return {
                "nodes_count": 0,
                "edges_count": 0,
                "pagerank": {},
                "betweenness": {},
                "degree_centrality": {},
                "communities": {},
                "top_influencers": [],
                "top_bridges": [],
                "annotated_nodes": []
            }

        pr_scores = compute_pagerank(graph_data)
        bw_scores = compute_betweenness(graph_data)
        deg_scores = compute_degree_centrality(graph_data)
        comm_res = detect_communities(graph_data)

        communities = comm_res.get("communities", {})
        node_communities = comm_res.get("node_communities", {})
        community_colors = comm_res.get("community_colors", {})

        # Build top 5 influencers by PageRank
        sorted_pr = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)
        top_influencers = [{"node_id": nid, "score": score} for nid, score in sorted_pr[:5]]

        # Build top 5 bridges by Betweenness
        sorted_bw = sorted(bw_scores.items(), key=lambda x: x[1], reverse=True)
        top_bridges = [{"node_id": nid, "score": score} for nid, score in sorted_bw[:5]]

        # Annotate node dicts with analytics properties
        annotated_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            n_copy["pagerank"] = pr_scores.get(nid, 0.0)
            n_copy["betweenness"] = bw_scores.get(nid, 0.0)
            n_copy["degree_centrality"] = deg_scores.get(nid, {})
            comm_id = node_communities.get(nid, "community_1")
            n_copy["community_id"] = comm_id
            n_copy["community_color"] = community_colors.get(comm_id, "#3B82F6")
            annotated_nodes.append(n_copy)

        return {
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "pagerank": pr_scores,
            "betweenness": bw_scores,
            "degree_centrality": deg_scores,
            "communities": communities,
            "community_colors": community_colors,
            "top_influencers": top_influencers,
            "top_bridges": top_bridges,
            "annotated_nodes": annotated_nodes
        }

    @staticmethod
    def get_shortest_path(graph_data: Dict[str, Any], source_id: str, target_id: str) -> Dict[str, Any]:
        """Finds shortest path sequence between source_id and target_id."""
        return find_shortest_path(graph_data, source_id, target_id)
