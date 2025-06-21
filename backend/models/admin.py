"""
Admin-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class PackageBase(BaseModel):
    name_ru: str = Field(..., min_length=2, max_length=100)
    name_ua: str = Field(..., min_length=2, max_length=100)
    package_type: str = Field(..., regex="^(job|service|all)$")
    price: float = Field(0, ge=0)
    currency_id: str
    duration_days: int = Field(30, ge=1, le=365)
    post_lifetime_days: int = Field(30, ge=1, le=365)
    features_ru: List[str] = []
    features_ua: List[str] = []
    has_photo: bool = False
    has_highlight: bool = False
    has_boost: bool = False
    boost_interval_days: Optional[int] = Field(None, ge=1, le=30)
    sort_order: int = Field(0, ge=0)

class PackageCreate(PackageBase):
    pass

class PackageUpdate(BaseModel):
    name_ru: Optional[str] = Field(None, min_length=2, max_length=100)
    name_ua: Optional[str] = Field(None, min_length=2, max_length=100)
    package_type: Optional[str] = Field(None, regex="^(job|service|all)$")
    price: Optional[float] = Field(None, ge=0)
    currency_id: Optional[str] = None
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    post_lifetime_days: Optional[int] = Field(None, ge=1, le=365)
    features_ru: Optional[List[str]] = None
    features_ua: Optional[List[str]] = None
    has_photo: Optional[bool] = None
    has_highlight: Optional[bool] = None
    has_boost: Optional[bool] = None
    boost_interval_days: Optional[int] = Field(None, ge=1, le=30)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class PackageResponse(PackageBase):
    id: str
    is_active: bool = True
    created_at: str
    updated_at: str

class CategoryBase(BaseModel):
    name_ru: str = Field(..., min_length=2, max_length=100)
    name_ua: str = Field(..., min_length=2, max_length=100)
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name_ru: Optional[str] = Field(None, min_length=2, max_length=100)
    name_ua: Optional[str] = Field(None, min_length=2, max_length=100)
    icon: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: str
    is_active: bool = True

class CityBase(BaseModel):
    name_ru: str = Field(..., min_length=2, max_length=100)
    name_ua: str = Field(..., min_length=2, max_length=100)

class CityCreate(CityBase):
    pass

class CityUpdate(BaseModel):
    name_ru: Optional[str] = Field(None, min_length=2, max_length=100)
    name_ua: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None

class CityResponse(CityBase):
    id: str
    is_active: bool = True