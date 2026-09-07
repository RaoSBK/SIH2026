# -*- coding: utf-8 -*-

from fastapi import APIRouter
from backend.app.api import auth, cases, users, evidence, entities, ingestion, review

router = APIRouter(prefix="/api")
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(cases.router, prefix="/cases", tags=["cases"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
router.include_router(entities.router, prefix="/entities", tags=["entities"])
router.include_router(ingestion.router, tags=["ingestion"])
router.include_router(review.router, tags=["review"])
