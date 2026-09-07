import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
SQLITE_DB_PATH = os.path.join(DATA_DIR, "cias.db")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    os.makedirs(DATA_DIR, exist_ok=True)
    DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# Configure engine arguments
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

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

class ReviewQueueModel(Base):
    __tablename__ = "review_queue"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(100), unique=True, index=True)
    case_id = Column(String(50), index=True)
    type_name = Column(String(50), default="AMBIGUITY")
    payload = Column(JSON, default=dict)
    status = Column(String(30), default="PENDING")  # PENDING, MERGED, REJECTED, SKIPPED
    created_at = Column(DateTime, default=datetime.utcnow)

# ─── Helper Functions ─────────────────────────────────────────────────────────

def init_db():
    """Initializes database schema tables."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        Base.metadata.create_all(bind=engine)
        logger.info(f"Initialized relational database schema using {DATABASE_URL}")
    except Exception as e:
        logger.error(f"Database schema initialization error: {e}")

def get_db_session():
    """Returns a new thread-local database session."""
    return SessionLocal()

def save_case_db(case_id: str, description: str = "") -> Dict[str, Any]:
    """Saves or updates a case context in the relational database."""
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
    """Returns all registered cases from the database."""
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

def save_audit_log_db(
    file_name: str,
    source_label: str = "unknown",
    case_id: Optional[str] = None,
    status: str = "success",
    message: str = "",
    entities_count: int = 0,
    new_nodes: int = 0
) -> Dict[str, Any]:
    """Persists an ingestion audit log record into the database."""
    session = SessionLocal()
    try:
        audit_entry = AuditLogModel(
            file_name=file_name,
            source_label=source_label,
            case_id=case_id or "unknown",
            status=status,
            message=message,
            entities_count=entities_count,
            new_nodes=new_nodes
        )
        session.add(audit_entry)
        session.commit()
        return {"status": "success", "id": audit_entry.id}
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving audit log to DB: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        session.close()

def get_audit_logs_db() -> List[Dict[str, Any]]:
    """Retrieves all audit log entries from the database."""
    session = SessionLocal()
    try:
        logs = session.query(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(100).all()
        return [{
            "id": l.id,
            "file_name": l.file_name,
            "source_label": l.source_label,
            "case_id": l.case_id,
            "status": l.status,
            "message": l.message,
            "entities_count": l.entities_count,
            "new_nodes": l.new_nodes,
            "timestamp": l.created_at.isoformat() if l.created_at else ""
        } for l in logs]
    except Exception as e:
        logger.error(f"Error reading audit logs from DB: {e}")
        return []
    finally:
        session.close()
