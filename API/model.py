# API/models.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# --- Import your SQLAlchemy model from RIA ---
# This line is crucial for your API folder to access the GitHubRepo definition
# and the Base object if it's defined in rain_class.py
from Class.rain_class import GitHubRepo, Base # Assuming Base is also defined/exported here

# --- Your Pydantic Repo model (as you provided) ---
class Repo(BaseModel):
    id: Optional[int] = None
    name: str
    owner: str
    owner_url: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    html_url: Optional[str] = None
    stargazers_count: Optional[int] = 0
    forks_count: Optional[int] = 0
    topics: Optional[List[str]] = []
    is_trending: Optional[bool] = False
    source: Optional[str] = None

    class Config:
        from_attributes = True # Important for Pydantic v2+
        json_schema_extra = {
            "example": {
                "id": 12345,
                "name": "my-awesome-repo",
                "owner": "john_doe",
                "description": "A cool project.",
                "stargazers_count": 100,
                "forks_count": 50,
                "topics": ["python", "fastapi"],
                "source": "github"
            }
        }

from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from .database import Base # Assurez-vous d'avoir une 'Base' déclarative dans db.py

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False) # nullable=True rend le champ optionnel
    last_name = Column(String(100), nullable=False)  # nullable=True rend le champ optionnel
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))