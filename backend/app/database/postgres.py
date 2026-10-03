from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config.settings import settings

if settings.database_url.startswith("sqlite"):
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes schema if needed."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

def save_case_db(case_id: str, description: str = ""):
    return {"case_id": case_id, "status": "exists"}

def get_cases_db():
    return []

def save_audit_log_db(file_name: str, source_label: str = "unknown", case_id=None, status="success", message="", entities_count=0, new_nodes=0):
    return {"status": "success"}

def get_audit_logs_db():
    return []
