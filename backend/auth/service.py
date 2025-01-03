from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import sqlite3
import os
from dotenv import load_dotenv
from .models import User, TokenData, UserCreate

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
AUTH_DB_PATH = os.getenv("AUTH_DB_PATH")

def get_db():
    conn = sqlite3.connect(AUTH_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: sqlite3.Connection, username: str) -> Optional[User]:
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    wefewf = cursor.fetchall()
    print(wefewf)
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    if user_data:
        return User(**dict(user_data))
    return None

def create_user(db: sqlite3.Connection, user: UserCreate) -> User:
    cursor = db.cursor()
    hashed_password = get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        (user.username, user.email, hashed_password)
    )
    db.commit()
    return get_user(db, user.username)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def authenticate_user(db: sqlite3.Connection, username: str, password: str) -> Optional[User]:
    user = get_user(db, username)
    if not user:
        return None
    cursor = db.cursor()
    cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    print(result)
    if not result or not verify_password(password, result["hashed_password"]):
        return None
    return user
