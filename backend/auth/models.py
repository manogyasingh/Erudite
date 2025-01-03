from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class KnowledgeGraphBase(BaseModel):
    title: str

class KnowledgeGraphCreate(KnowledgeGraphBase):
    user_id: int

    @classmethod
    def create_new(cls, title: str, user_id: int):
        return cls(
            title=title,
            user_id=user_id,
            uuid=str(uuid.uuid4())
        )

class KnowledgeGraph(KnowledgeGraphBase):
    id: int
    uuid: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
