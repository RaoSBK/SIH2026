import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True) if not settings.database_url.startswith("sqlite") else create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── ORM Models ───────────────────────────────────────────────────────────────

class CaseModel(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="ACTIVE")

class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), index=True, nullable=False)
    case_id = Column(String(50), index=True, nullable=False)
    file_type = Column(String(20), default="unknown")
    sha256 = Column(String(64), default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="PROCESSED")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), index=True)
    source_label = Column(String(100), default="unknown")
    case_id = Column(String(50), index=True)
    status = Column(String(50), default="success")
    message = Column(Text, default="")
    entities_count = Column(Integer, default=0)
    new_nodes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initializes database schema tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Initialized relational database schema")
    except Exception as e:
        logger.error(f"Database schema initialization error: {e}")

def save_case_db(case_id: str, description: str = "") -> Dict[str, Any]:
    session = SessionLocal()
    try:
        c_id = case_id.strip().upper()
        if not c_id.startswith("CASE-"):
            c_id = f"CASE-{c_id}"

        existing = session.query(CaseModel).filter_by(case_id=c_id).first()
        if not existing:
            new_case = CaseModel(case_id=c_id, description=description)
            session.add(new_case)
            session.commit()
            return {"case_id": c_id, "status": "created"}
        return {"case_id": c_id, "status": "exists"}
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving case {case_id} to DB: {e}")
        return {"case_id": case_id, "status": "error", "error": str(e)}
    finally:
        session.close()

def get_cases_db() -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        cases = session.query(CaseModel).all()
        result = []
        for c in cases:
            docs = session.query(DocumentModel).filter_by(case_id=c.case_id).all()
            files = [d.file_name for d in docs]
            result.append({
                "case_id": c.case_id,
                "description": c.description,
                "document_count": len(files),
                "files": files,
                "created_at": c.created_at.isoformat() if c.created_at else ""
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching cases from DB: {e}")
        return []
    finally:
        session.close()
