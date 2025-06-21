"""
Post-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    price: Optional[float] = Field(None, ge=0)
    currency_id: Optional[str] = None
    city_id: str
    super_rubric_id: str

class PostCreate(PostBase):
    package_id: Optional[str] = None

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    price: Optional[float] = Field(None, ge=0)
    currency_id: Optional[str] = None
    city_id: Optional[str] = None
    super_rubric_id: Optional[str] = None
    status: Optional[int] = Field(None, ge=1, le=5)

class PostResponse(PostBase):
    id: str
    post_type: str
    author_id: str
    status: int
    has_photo: bool = False
    has_highlight: bool = False
    has_boost: bool = False
    views_count: int = 0
    is_premium: bool = False
    ai_moderation_passed: bool = False
    created_at: str
    updated_at: str
    expires_at: str

class PostFilter(BaseModel):
    post_type: Optional[str] = None
    search: Optional[str] = None
    author_id: Optional[str] = None
    super_rubric_id: Optional[str] = None
    city_id: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=50)