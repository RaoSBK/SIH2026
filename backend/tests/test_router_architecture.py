import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from uuid import uuid4
from backend.app.auth.rbac import get_current_user
from backend.app.database.postgres import get_db, Base
from backend.app.cases.models import Case, CaseAssignment  # noqa: F401
from backend.app.users.models import User  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

mock_user = User(id=uuid4(), username="testuser", role="supervisor")
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

from uuid import uuid4
from backend.app.auth.rbac import get_current_user
from backend.app.database.postgres import get_db
from backend.app.users.models import User

def mock_get_current_user():
    return User(id=uuid4(), username="admin", role="supervisor")

def test_cases_router_endpoints(db_session):
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    res1 = client.get("/api/cases")
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    res2 = client.post("/api/cases", json={"case_id": "CASE-999", "title": "Test", "description": "Desc"})
    assert res2.status_code == 200
    assert res2.json()["case_id"] == "CASE-999"

    res3 = client.get("/api/cases/CASE-102/graph")
    assert res3.status_code == 200

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = override_get_db

def test_entities_router_endpoints():
    res1 = client.get("/api/needs-review")
    assert res1.status_code == 200

    res2 = client.get("/api/review-queue")
    assert res2.status_code == 200
    assert "pending_review" in res2.json()

def test_audit_router_endpoints():
    res1 = client.get("/api/ingestion-audit")
    assert res1.status_code == 200

    res2 = client.get("/api/filtered-edges")
    assert res2.status_code == 200

def test_graph_router_endpoints():
    res1 = client.get("/api/graph/schema")
    assert res1.status_code == 200
