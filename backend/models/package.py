from enum import Enum
from typing import Optional
from pydantic import BaseModel
from models.base import BaseDocument

class PackageType(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"

class Package(BaseDocument):
    name_ru: str
    name_ua: str
    package_type: PackageType
    price: float
    currency_id: str
    duration_days: int
    features_ru: list[str]
    features_ua: list[str]
    is_active: bool = True

class Payment(BaseDocument):
    user_id: str
    post_id: str
    package_id: str
    amount: float
    currency_id: str
    telegram_payment_charge_id: Optional[str] = None
    provider_payment_charge_id: Optional[str] = None
    status: str = "pending"  # pending, completed, failed, refunded

# Create schemas
class PackageCreate(BaseModel):
    name_ru: str
    name_ua: str
    package_type: PackageType
    price: float
    currency_id: str
    duration_days: int
    features_ru: list[str]
    features_ua: list[str]

class PaymentCreate(BaseModel):
    post_id: str
    package_id: str