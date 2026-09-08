# -*- coding: utf-8 -*-

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.postgres import Base
from backend.app.users.models import User
from backend.app.auth.authentication import hash_password, verify_password

# Use in-memory SQLite for isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_password_hashing():
    plain_password = "supersecretpassword123!"
    hashed = hash_password(plain_password)
    
    assert hashed != plain_password
    assert verify_password(plain_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_user_creation(db_session):
    plain_password = "testpassword"
    hashed = hash_password(plain_password)
    
    user = User(
        username="testuser",
        hashed_password=hashed,
        full_name="Test User",
        role="investigator"
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.role == "investigator"
    assert user.is_active is True
    assert user.created_at is not None
    
    # Retrieve from DB to ensure it persisted correctly
    retrieved_user = db_session.query(User).filter(User.username == "testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert verify_password(plain_password, retrieved_user.hashed_password) is True

def test_jwt_creation_and_decoding():
    from backend.app.auth.jwt import create_access_token, decode_access_token
    from datetime import timedelta
    from jose import JWTError

    data = {"sub": "testuser", "role": "investigator"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "investigator"
    assert "exp" in decoded

def test_jwt_expired_token():
    from backend.app.auth.jwt import create_access_token, decode_access_token
    from datetime import timedelta
    from jose import JWTError, ExpiredSignatureError
    import time
    
    # Create an expired token (by setting a negative delta, jose will catch it)
    data = {"sub": "testuser", "role": "investigator"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(ExpiredSignatureError):
        decode_access_token(token)

def test_jwt_invalid_token():
    from backend.app.auth.jwt import decode_access_token
    from jose import JWTError
    
    with pytest.raises(JWTError):
        decode_access_token("invalid.token.string")
