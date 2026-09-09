import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import backend.app.database.postgres as postgres_module
from backend.app.database.postgres import Base
from backend.app.users.models import User
from backend.app.cases.models import Case, CaseAssignment
from backend.app.evidence.models import EvidenceFile

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override engine and SessionLocal in postgres module so background calls use the same DB
    postgres_module.engine = engine
    postgres_module.SessionLocal = TestingSessionLocal
    
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
