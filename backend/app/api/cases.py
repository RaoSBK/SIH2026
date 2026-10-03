# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.app.database.postgres import get_db
from backend.app.auth.rbac import get_current_user, require_role
from backend.app.auth.abac import require_case_access
from backend.app.users.models import User
from backend.app.cases import service
from backend.app.cases.schemas import CaseCreate, CaseOut, CaseAssign

router = APIRouter()

@router.post("", response_model=CaseOut, dependencies=[Depends(require_role("investigator", "supervisor", "system_admin"))])
def create_case(
    case_in: CaseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return service.create_case(db, case_in, current_user.id)

@router.get("", response_model=List[CaseOut])
def list_cases(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return service.get_cases(db, current_user.id, current_user.role)

@router.get("/{case_id}", response_model=CaseOut, dependencies=[Depends(require_case_access)])
def get_case(
    case_id: str, 
    db: Session = Depends(get_db)
):
    case = service.get_case(db, case_id)
    if not case:
        raise not_found("Case not found")
    return case

@router.get("/{case_id}/graph", dependencies=[Depends(require_case_access)])
def get_case_graph(case_id: str):
    import logging
    from fastapi import HTTPException
    logger = logging.getLogger(__name__)
    from backend.app.database.neo4j import driver as neo4j_driver
    try:
        with neo4j_driver.session() as session:
            nodes_result = session.run(
                "MATCH (n) WHERE NOT n:Document AND n.id IS NOT NULL AND (n.case_id = $case_id OR (n)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})) "
                "RETURN DISTINCT n.id AS id, coalesce(n.value, n.name, n.id) AS value, "
                "       coalesce(n.type, [lbl IN labels(n) WHERE lbl <> 'Entity'][0], labels(n)[0]) AS type, "
                "       n.confidence AS confidence, "
                "       n.status AS status, n.risk_color AS risk_color, "
                "       n.historical_firs AS historical_firs, "
                "       n.phone AS phone, n.anomaly_reasons AS anomaly_reasons, "
                "       n.evidence_trail AS evidence_trail, n.flagged AS flagged",
                case_id=case_id
            )
            nodes = [dict(r) for r in nodes_result]

            edges_result = session.run(
                "MATCH (a) WHERE NOT a:Document AND a.id IS NOT NULL AND (a.case_id = $case_id OR (a)-[:EXTRACTED_FROM]->(:Document {case_id: $case_id})) "
                "MATCH (a)-[r]->(b) WHERE NOT b:Document AND b.id IS NOT NULL AND type(r) <> 'EXTRACTED_FROM' "
                "RETURN DISTINCT a.id AS source, b.id AS target, type(r) AS type, "
                "       coalesce(r.relationship_type, CASE WHEN type(r) IN ['CALLED','CALL','CALLING'] THEN 'calling' ELSE type(r) END) AS relationship_type, "
                "       r.confidence AS confidence, r.status AS status, r.evidence AS evidence",
                case_id=case_id
            )
            edges = [dict(r) for r in edges_result]

        valid_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in valid_ids and e["target"] in valid_ids]

        return {"nodes": nodes, "edges": edges, "case_id": case_id}
    except Exception as e:
        logger.error(f"[get_case_graph] Failed for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve graph data for case {case_id}: {str(e)}")

@router.post("/{case_id}/assign", dependencies=[Depends(require_role("supervisor"))])
def assign_case(
    case_id: str, 
    assign_in: CaseAssign, 
    db: Session = Depends(get_db)
):
    service.assign_user(db, case_id, assign_in.user_id)
    return {"status": "success", "message": f"User {assign_in.user_id} assigned to case {case_id}"}
