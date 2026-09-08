# -*- coding: utf-8 -*-

from sqlalchemy.orm import Session
from backend.app.users.models import User
from backend.app.users.schemas import UserCreate
from backend.app.auth.authentication import hash_password
from backend.app.utils.exceptions import bad_request, not_found
from uuid import UUID

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user_in: UserCreate):
    existing = get_user_by_username(db, user_in.username)
    if existing:
        raise bad_request("Username already registered")
        
    hashed_password = hash_password(user_in.password)
    user = User(
        username=user_in.username,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_users(db: Session):
    return db.query(User).all()

def update_user_role(db: Session, user_id: UUID, role: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise not_found("User not found")
        
    user.role = role
    db.commit()
    db.refresh(user)
    return user
