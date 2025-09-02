# Fichier: API/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str  
    last_name: str   

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    first_name: str  
    last_name: str   

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None