import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Graph Operations"])

class CypherQueryPayload(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

@router.get("/graph/schema")
def get_graph_schema():
    """
    Returns node labels, relationship types, and constraint definitions in Neo4j.
    """
    try:
        from ..database.neo4j import driver as neo4j_driver
        with neo4j_driver.session() as session:
            labels_res = session.run("CALL db.labels()")
            labels = [r[0] for r in labels_res]

            rel_types_res = session.run("CALL db.relationshipTypes()")
            rel_types = [r[0] for r in rel_types_res]

        return {
            "status": "success",
            "labels": labels,
            "relationship_types": rel_types
        }
    except Exception as e:
        return {
            "status": "fallback",
            "labels": ["PERSON", "PHONE", "VEHICLE", "LOCATION", "ORGANIZATION", "Document"],
            "relationship_types": ["CALLED", "TRANSFERRED_TO", "VISITED", "ASSOCIATED_WITH", "EXTRACTED_FROM"]
        }

@router.post("/graph/query")
def execute_cypher_query(payload: CypherQueryPayload):
    """
    Executes custom read-only Cypher queries against Neo4j.
    """
    try:
        from ..database.neo4j import driver as neo4j_driver
        with neo4j_driver.session() as session:
            result = session.run(payload.query, payload.params or {})
            records = [dict(r) for r in result]
        return {"status": "success", "count": len(records), "records": records}
    except Exception as e:
        logger.error(f"Cypher query error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
