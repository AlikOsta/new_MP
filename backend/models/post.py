from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from models.base import BaseDocument

class PostStatus(int, Enum):
    DRAFT = 1
    MODERATION = 2
    ACTIVE = 3
    BLOCKED = 4
    EXPIRED = 5

class WorkExperience(str, Enum):
    NO_EXPERIENCE = "no_experience"
    UP_TO_1_YEAR = "up_to_1_year"
    FROM_1_TO_3_YEARS = "from_1_to_3_years"
    FROM_3_TO_6_YEARS = "from_3_to_6_years"
    MORE_THAN_6_YEARS = "more_than_6_years"

class WorkSchedule(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    PROJECT = "project"
    FREELANCE = "freelance"

class WorkFormat(str, Enum):
    OFFICE = "office"
    REMOTE = "remote"
    HYBRID = "hybrid"

class AbsPost(BaseDocument):
    title: str
    description: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency_id: str
    super_rubric_id: str
    sub_rubric_id: Optional[str] = None
    city_id: str
    author_id: str
    phone: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    is_premium: bool = False
    views_count: int = 0
    post_type: str  # "job" or "service"

class PostJob(AbsPost):
    post_type: str = "job"
    experience: Optional[WorkExperience] = None
    schedule: Optional[WorkSchedule] = None
    work_format: Optional[WorkFormat] = None

class PostServices(AbsPost):
    post_type: str = "service"

class Favorite(BaseDocument):
    user_id: str
    post_id: str

# Create/Update schemas
class PostJobCreate(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency_id: str
    super_rubric_id: str
    sub_rubric_id: Optional[str] = None
    city_id: str
    phone: Optional[str] = None
    experience: Optional[WorkExperience] = None
    schedule: Optional[WorkSchedule] = None
    work_format: Optional[WorkFormat] = None

class PostServicesCreate(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency_id: str
    super_rubric_id: str
    sub_rubric_id: Optional[str] = None
    city_id: str
    phone: Optional[str] = None

class PostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency_id: Optional[str] = None
    city_id: Optional[str] = None
    phone: Optional[str] = None