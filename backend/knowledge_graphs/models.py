from pydantic import BaseModel
from datetime import datetime
from auth.models import User

class KnowledgeGraphBase(BaseModel):
    title: str

class KnowledgeGraphCreate(KnowledgeGraphBase):
    user_id: int
    pass

class KnowledgeGraph(KnowledgeGraphBase):
    uuid: str
    user_id: int
    
    class Config:
        from_attributes = True  # Updated from orm_mode which is deprecated in Pydantic v2
