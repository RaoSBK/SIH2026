from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
import asyncio
import json

from .ingestion.service import process_file
from ml.anomaly.anomaly_rules import run_rule_engine
from ml.anomaly.anomaly_ml import run_ml_engine

from fastapi import Depends
from backend.app.users.models import User
from backend.app.auth.rbac import get_current_user, require_role
from backend.app.auth.abac import require_case_access

app = FastAPI(title="CIAS ML Backend")

from backend.app.api.router import router
app.include_router(router)

@app.on_event("startup")
def startup_event():
    from .database.postgres import Base, engine, SessionLocal
    Base.metadata.create_all(bind=engine)
    
    # Seed default user rao.a
    from backend.app.users.models import User
    from backend.app.auth.authentication import hash_password
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "rao.a").first()
        if not user:
            new_user = User(
                username="rao.a",
                hashed_password=hash_password("veritas"),
                role="investigator",
                full_name="Inspector Arjun Rao"
            )
            db.add(new_user)
            db.commit()
    finally:
        db.close()


# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local dev — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "CIAS ML Backend"}

import logging

logger = logging.getLogger(__name__)

# Legacy endpoints migrated to api routers.
