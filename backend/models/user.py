"""
User-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = "ru"

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_active: bool = True
    created_at: str
    updated_at: str

class FavoriteCreate(BaseModel):
    user_id: str
    post_id: str

class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    post_id: str
    created_at: str