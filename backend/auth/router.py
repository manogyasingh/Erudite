import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from .service import (
    authenticate_user, create_access_token, get_db,
    ACCESS_TOKEN_EXPIRE_MINUTES, create_user, get_current_user
)
from .models import User, Token, UserCreate

router = APIRouter(prefix="", tags=["auth"])

@router.post("/auth/token", response_model=Token)
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/register", response_model=User)
async def register_user(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    db_user = create_user(db, user)
    return db_user

@router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
