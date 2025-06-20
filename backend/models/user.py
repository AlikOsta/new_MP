from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from models.base import BaseDocument

class Language(str, Enum):
    RU = "ru"
    UA = "ua"

class ColorScheme(str, Enum):
    LIGHT = "light"
    DARK = "dark"

class TelegramUser(BaseDocument):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    language: Language = Language.RU
    city_id: Optional[str] = None
    color_scheme: ColorScheme = ColorScheme.LIGHT
    is_active: bool = True
    free_posts_this_week: int = 1
    
class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[Language] = None
    city_id: Optional[str] = None
    color_scheme: Optional[ColorScheme] = None