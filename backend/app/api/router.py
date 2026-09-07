from fastapi import APIRouter

from .cases import router as cases_router
from .ingestion import router as ingestion_router
from .entities import router as entities_router
from .audit import router as audit_router
from .graph import router as graph_router
from .anomaly import router as anomaly_router
from .analytics import router as analytics_router
from .evidence import router as evidence_router

api_router = APIRouter()

api_router.include_router(cases_router)
api_router.include_router(ingestion_router)
api_router.include_router(entities_router)
api_router.include_router(audit_router)
api_router.include_router(graph_router)
api_router.include_router(anomaly_router)
api_router.include_router(analytics_router)
api_router.include_router(evidence_router)
