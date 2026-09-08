# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database.postgres import get_db
from backend.app.users.schemas import UserCreate, UserOut
from backend.app.users import service as user_service
from backend.app.auth.authentication import verify_password
from backend.app.auth.jwt import create_access_token
from backend.app.auth.rbac import get_current_user
from backend.app.utils.exceptions import forbidden
from backend.app.users.models import User

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user_in)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_service.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise forbidden("Incorrect username or password")
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
