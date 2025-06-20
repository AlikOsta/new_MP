from typing import Optional, List
from pydantic import BaseModel
from models.base import BaseDocument

class SuperRubric(BaseDocument):
    name_ru: str
    name_ua: str
    icon: Optional[str] = None
    is_active: bool = True

class SubRubric(BaseDocument):
    name_ru: str
    name_ua: str
    super_rubric_id: str
    is_active: bool = True

class City(BaseDocument):
    name_ru: str
    name_ua: str
    is_active: bool = True

class Currency(BaseDocument):
    code: str  # USD, EUR, RUB, UAH
    name_ru: str
    name_ua: str
    symbol: str
    is_active: bool = True

# Create/Update schemas
class SuperRubricCreate(BaseModel):
    name_ru: str
    name_ua: str
    icon: Optional[str] = None

class SubRubricCreate(BaseModel):
    name_ru: str
    name_ua: str
    super_rubric_id: str

class CityCreate(BaseModel):
    name_ru: str
    name_ua: str

class CurrencyCreate(BaseModel):
    code: str
    name_ru: str
    name_ua: str
    symbol: str