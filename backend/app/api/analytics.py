import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from graph.services.analytics_service import GraphAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Graph Analytics"])

class AnalyticsGraphPayload(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

@router.get("/cases/{case_id}/analytics")
def get_case_analytics(case_id: str):
    """
    Computes NetworkX graph analytics (PageRank, Betweenness, Communities, Degrees)
    for a given case's graph network.
    """
    from .cases import get_case_graph

    graph_res = get_case_graph(case_id)
    nodes = graph_res.get("nodes", [])
    edges = graph_res.get("edges", [])

    if not nodes:
        return {
            "case_id": case_id,
            "nodes_count": 0,
            "edges_count": 0,
            "pagerank": {},
            "betweenness": {},
            "communities": {},
            "top_influencers": [],
            "top_bridges": []
        }

    graph_payload = {"nodes": nodes, "edges": edges}
    try:
        analytics = GraphAnalyticsService.run_full_analytics(graph_payload)
        analytics["case_id"] = case_id
        return analytics
    except Exception as e:
        logger.error(f"Failed to compute case analytics for {case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics execution failed: {str(e)}")

@router.post("/analytics/run")
def run_custom_graph_analytics(payload: AnalyticsGraphPayload):
    """
    Runs graph analytics on any arbitrary incoming graph payload.
    """
    graph_payload = {"nodes": payload.nodes, "edges": payload.edges}
    try:
        analytics = GraphAnalyticsService.run_full_analytics(graph_payload)
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        logger.error(f"Failed to run graph analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/shortest-path")
def get_shortest_path_endpoint(case_id: str, source: str = Query(...), target: str = Query(...)):
    """
    Finds the shortest network path sequence and distance between source and target entities.
    """
    from .cases import get_case_graph

    graph_res = get_case_graph(case_id)
    nodes = graph_res.get("nodes", [])
    edges = graph_res.get("edges", [])

    graph_payload = {"nodes": nodes, "edges": edges}
    path_result = GraphAnalyticsService.get_shortest_path(graph_payload, source, target)
    return path_result
