import sys
import os
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple database connection
client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client[os.getenv("DB_NAME", "telegram_marketplace")]

# Simple dependency
async def get_database():
    return db

# Import API routers with simple approach
from fastapi import APIRouter

# Categories router
categories_router = APIRouter(prefix="/api/categories", tags=["categories"])

@categories_router.get("/super-rubrics")
async def get_super_rubrics():
    results = await db.fetchall("SELECT * FROM super_rubrics WHERE is_active = 1")
    return results

@categories_router.get("/cities")
async def get_cities():
    results = await db.fetchall("SELECT * FROM cities WHERE is_active = 1")
    return results

@categories_router.get("/currencies")
async def get_currencies():
    results = await db.fetchall("SELECT * FROM currencies WHERE is_active = 1")
    return results

# Posts router
posts_router = APIRouter(prefix="/api/posts", tags=["posts"])

@posts_router.get("/")
async def get_posts(
    post_type: str = None, 
    search: str = None, 
    author_id: str = None,
    super_rubric_id: str = None,
    city_id: str = None
):
    query = {"status": 3}  # Active status по умолчанию
    
    # Если запрашиваются посты конкретного автора, показываем все статусы
    if author_id:
        query = {"author_id": author_id}
    else:
        query = {"status": 3}  # Для общего списка только активные
    
    if post_type:
        query["post_type"] = post_type
    if super_rubric_id:
        query["super_rubric_id"] = super_rubric_id
    if city_id:
        query["city_id"] = city_id
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.posts.find(query).sort("created_at", -1).limit(50)
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

@posts_router.post("/jobs")
async def create_job_post(request: Request):
    """Create a job post"""
    data = await request.json()
    
    # Add additional fields
    data["post_type"] = "job"
    data["status"] = 3  # Active status (вместо 1 - Draft)
    data["views_count"] = 0
    data["is_premium"] = False
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    
    # Get author_id from header
    author_id = request.headers.get("X-Author-ID", "demo-user")
    data["author_id"] = author_id
    
    result = await db.posts.insert_one(data)
    created_post = await db.posts.find_one({"_id": result.inserted_id})
    created_post["_id"] = str(created_post["_id"])
    created_post["id"] = created_post["_id"]
    
    return created_post

@posts_router.post("/services")
async def create_service_post(request: Request):
    """Create a service post"""
    data = await request.json()
    
    # Add additional fields
    data["post_type"] = "service"
    data["status"] = 3  # Active status (вместо 1 - Draft)
    data["views_count"] = 0
    data["is_premium"] = False
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    
    # Get author_id from header
    author_id = request.headers.get("X-Author-ID", "demo-user")
    data["author_id"] = author_id
    
    result = await db.posts.insert_one(data)
    created_post = await db.posts.find_one({"_id": result.inserted_id})
    created_post["_id"] = str(created_post["_id"])
    created_post["id"] = created_post["_id"]
    
    return created_post

@posts_router.put("/{post_id}/status")
async def update_post_status(post_id: str, request: Request):
    """Update post status"""
    from bson import ObjectId
    data = await request.json()
    status = data.get("status", 3)
    
    try:
        object_id = ObjectId(post_id)
    except:
        return {"error": "Invalid post ID"}
    
    result = await db.posts.update_one(
        {"_id": object_id},
        {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
    )
    
    if result.matched_count == 0:
        return {"error": "Post not found"}
    
    return {"message": "Status updated successfully"}

# Favorites endpoints
@posts_router.post("/favorites")
async def add_to_favorites(request: Request):
    """Add post to favorites"""
    data = await request.json()
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    
    if not user_id or not post_id:
        return {"error": "user_id and post_id are required"}
    
    # Check if already in favorites
    existing = await db.favorites.find_one({"user_id": user_id, "post_id": post_id})
    if existing:
        return {"error": "Already in favorites"}
    
    favorite_dict = {
        "user_id": user_id, 
        "post_id": post_id,
        "created_at": datetime.now().isoformat()
    }
    await db.favorites.insert_one(favorite_dict)
    return {"message": "Added to favorites"}

@posts_router.delete("/favorites")
async def remove_from_favorites(request: Request):
    """Remove post from favorites"""
    data = await request.json()
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    
    if not user_id or not post_id:
        return {"error": "user_id and post_id are required"}
    
    result = await db.favorites.delete_one({"user_id": user_id, "post_id": post_id})
    if result.deleted_count == 0:
        return {"error": "Not in favorites"}
    return {"message": "Removed from favorites"}

@posts_router.get("/favorites/{user_id}")
async def get_user_favorites(user_id: str):
    """Get user's favorite posts"""
    from bson import ObjectId
    
    # Get favorite post IDs
    cursor = db.favorites.find({"user_id": user_id})
    post_ids = [fav["post_id"] async for fav in cursor]
    
    if not post_ids:
        return []
    
    # Convert string IDs to ObjectIds for MongoDB query
    object_ids = []
    for post_id in post_ids:
        try:
            object_ids.append(ObjectId(post_id))
        except:
            continue  # Skip invalid IDs
    
    if not object_ids:
        return []
    
    # Get posts
    cursor = db.posts.find({"_id": {"$in": object_ids}})
    posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        posts.append(doc)
    
    return posts

@posts_router.get("/{post_id}")
async def get_post_details(post_id: str, user_id: str = None):
    """Get post details and increment views if not viewed by this user"""
    from bson import ObjectId
    
    try:
        object_id = ObjectId(post_id)
    except:
        return {"error": "Invalid post ID"}
    
    post = await db.posts.find_one({"_id": object_id})
    if not post:
        return {"error": "Post not found"}
    
    # Increment views only if user hasn't viewed this post before
    if user_id:
        # Check if user has already viewed this post
        existing_view = await db.post_views.find_one({
            "post_id": post_id, 
            "user_id": user_id
        })
        
        if not existing_view:
            # Increment views and record this view
            await db.posts.update_one(
                {"_id": object_id},
                {"$inc": {"views_count": 1}}
            )
            
            # Record that this user viewed this post
            await db.post_views.insert_one({
                "post_id": post_id,
                "user_id": user_id,
                "viewed_at": datetime.now().isoformat()
            })
            
            post["views_count"] = post.get("views_count", 0) + 1
    
    # Return post details
    post["_id"] = str(post["_id"])
    post["id"] = post["_id"]
    
    return post

# Admin router
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# Simple admin authentication (in production use proper JWT)
ADMIN_CREDENTIALS = {
    "username": "Admin",
    "password": "Admin"  # In production, use hashed passwords
}

@admin_router.post("/login")
async def admin_login(request: Request):
    """Admin login"""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    if username == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
        # In production, generate JWT token
        return {
            "success": True,
            "token": "admin_token_123",
            "user": {"username": username, "role": "admin"}
        }
    
    return {"success": False, "error": "Invalid credentials"}

@admin_router.get("/settings")
async def get_app_settings():
    """Get application settings"""
    settings = await db.app_settings.find_one({}) or {}
    
    default_settings = {
        "show_view_counts": True,
        "telegram_bot_token": "***hidden***",
        "mistral_api_key": "***hidden***",
        "app_name": "Telegram Marketplace",
        "app_description": "Платформа частных объявлений",
        "free_posts_per_week": 1,
        "moderation_enabled": True
    }
    
    # Merge with defaults and remove _id field to avoid serialization issues
    result = {**default_settings, **{k: v for k, v in settings.items() if k != "_id"}}
    result["id"] = str(settings.get("_id", "default"))
    
    return result

@admin_router.put("/settings")
async def update_app_settings(request: Request):
    """Update application settings"""
    data = await request.json()
    
    # Remove sensitive fields for logging
    safe_data = {k: v for k, v in data.items() if k not in ["telegram_bot_token", "mistral_api_key"]}
    print(f"Updating settings: {safe_data}")
    
    data["updated_at"] = datetime.now().isoformat()
    
    result = await db.app_settings.update_one(
        {},
        {"$set": data},
        upsert=True
    )
    
    return {"success": True, "message": "Settings updated"}

# Statistics endpoints
@admin_router.get("/stats/users")
async def get_user_stats():
    """Get user statistics"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # Total users
    total_users = await db.users.count_documents({})
    
    # New users last 7 days
    new_users_7d = await db.users.count_documents({
        "created_at": {"$gte": last_7_days.isoformat()}
    })
    
    # New users last 30 days
    new_users_30d = await db.users.count_documents({
        "created_at": {"$gte": last_30_days.isoformat()}
    })
    
    # Daily new users for chart (last 7 days)
    daily_users = []
    for i in range(7):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = await db.users.count_documents({
            "created_at": {
                "$gte": day_start.isoformat(),
                "$lt": day_end.isoformat()
            }
        })
        
        daily_users.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "total_users": total_users,
        "new_users_7d": new_users_7d,
        "new_users_30d": new_users_30d,
        "daily_users": list(reversed(daily_users))
    }

@admin_router.get("/stats/posts")
async def get_post_stats():
    """Get post statistics"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # Total posts
    total_posts = await db.posts.count_documents({})
    active_posts = await db.posts.count_documents({"status": 3})
    
    # New posts last 7 days
    new_posts_7d = await db.posts.count_documents({
        "created_at": {"$gte": last_7_days.isoformat()}
    })
    
    # New posts last 30 days
    new_posts_30d = await db.posts.count_documents({
        "created_at": {"$gte": last_30_days.isoformat()}
    })
    
    # Most popular posts (by views)
    cursor = db.posts.find({"status": 3}).sort("views_count", -1).limit(10)
    popular_posts = []
    async for post in cursor:
        # Get favorites count
        favorites_count = await db.favorites.count_documents({"post_id": str(post["_id"])})
        
        popular_posts.append({
            "id": str(post["_id"]),
            "title": post["title"],
            "views_count": post.get("views_count", 0),
            "favorites_count": favorites_count,
            "author_id": post.get("author_id", "")
        })
    
    # Posts by type
    job_posts = await db.posts.count_documents({"post_type": "job"})
    service_posts = await db.posts.count_documents({"post_type": "service"})
    
    return {
        "total_posts": total_posts,
        "active_posts": active_posts,
        "new_posts_7d": new_posts_7d,
        "new_posts_30d": new_posts_30d,
        "popular_posts": popular_posts,
        "posts_by_type": {
            "job": job_posts,
            "service": service_posts
        }
    }

# CRUD endpoints for admin management
@admin_router.get("/currencies")
async def admin_get_currencies():
    """Get all currencies for admin"""
    cursor = db.currencies.find({})
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

@admin_router.post("/currencies")
async def admin_create_currency(request: Request):
    """Create currency"""
    data = await request.json()
    data["created_at"] = datetime.now().isoformat()
    data["is_active"] = True
    
    result = await db.currencies.insert_one(data)
    created_currency = await db.currencies.find_one({"_id": result.inserted_id})
    created_currency["_id"] = str(created_currency["_id"])
    created_currency["id"] = created_currency["_id"]
    
    return created_currency

@admin_router.put("/currencies/{currency_id}")
async def admin_update_currency(currency_id: str, request: Request):
    """Update currency"""
    from bson import ObjectId
    data = await request.json()
    data["updated_at"] = datetime.now().isoformat()
    
    try:
        object_id = ObjectId(currency_id)
    except:
        return {"error": "Invalid currency ID"}
    
    result = await db.currencies.update_one(
        {"_id": object_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        return {"error": "Currency not found"}
    
    return {"success": True, "message": "Currency updated"}

@admin_router.delete("/currencies/{currency_id}")
async def admin_delete_currency(currency_id: str):
    """Delete currency"""
    from bson import ObjectId
    
    try:
        object_id = ObjectId(currency_id)
    except:
        return {"error": "Invalid currency ID"}
    
    result = await db.currencies.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        return {"error": "Currency not found"}
    
    return {"success": True, "message": "Currency deleted"}

# Users router
users_router = APIRouter(prefix="/api/users", tags=["users"])

@users_router.post("/")
async def create_user(request: Request):
    """Create a new user"""
    data = await request.json()
    
    # Check if user already exists by telegram_id
    existing_user = await db.users.find_one({"telegram_id": data.get("telegram_id")})
    if existing_user:
        existing_user["id"] = str(existing_user["_id"])
        existing_user["_id"] = str(existing_user["_id"])
        return existing_user
    
    # Add default fields
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    data["is_active"] = True
    data["language"] = data.get("language", "ru")
    data["theme"] = data.get("theme", "light")
    
    result = await db.users.insert_one(data)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    created_user["id"] = str(created_user["_id"])
    created_user["_id"] = str(created_user["_id"])
    
    return created_user

@users_router.get("/{user_id}")
async def get_user(user_id: str):
    from bson import ObjectId
    
    try:
        # Try as ObjectId first
        object_id = ObjectId(user_id)
        user = await db.users.find_one({"_id": object_id})
    except:
        # If that fails, try as string
        user = await db.users.find_one({"_id": user_id})
    
    if user:
        user["id"] = str(user["_id"])
        user["_id"] = str(user["_id"])
        return user
    return {"error": "User not found"}

@users_router.put("/{user_id}")
async def update_user(user_id: str, request: Request):
    """Update user profile"""
    data = await request.json()
    
    # Remove None values
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return {"error": "No data to update"}
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return {"error": "User not found"}
    
    updated_user = await db.users.find_one({"_id": user_id})
    updated_user["id"] = str(updated_user["_id"])
    return updated_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize default data
    await initialize_default_data()
    yield
    # Shutdown - Database connection is handled in database.py

app = FastAPI(
    title="Telegram Marketplace API",
    description="API for Telegram Mini App - Private Listings Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(categories_router)
app.include_router(posts_router)
app.include_router(admin_router)
app.include_router(users_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Telegram Marketplace API is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook endpoint (placeholder)"""
    return {"ok": True}

@app.get("/")
async def root():
    return {"message": "Telegram Marketplace API", "docs": "/docs"}

async def initialize_default_data():
    """Initialize default categories, currencies, and packages"""
    # Check if data already exists
    if await db.super_rubrics.count_documents({}) > 0:
        return
    
    # Create default currencies
    currencies = [
        {"_id": "rub-id", "code": "RUB", "name_ru": "Российский рубль", "name_ua": "Російський рубль", "symbol": "₽", "is_active": True},
        {"_id": "usd-id", "code": "USD", "name_ru": "Доллар США", "name_ua": "Долар США", "symbol": "$", "is_active": True},
        {"_id": "eur-id", "code": "EUR", "name_ru": "Евро", "name_ua": "Євро", "symbol": "€", "is_active": True},
        {"_id": "uah-id", "code": "UAH", "name_ru": "Украинская гривна", "name_ua": "Українська гривня", "symbol": "₴", "is_active": True},
    ]
    
    for currency in currencies:
        await db.currencies.insert_one(currency)
    
    # Create default super rubrics
    super_rubrics = [
        {"_id": "job-rubric", "name_ru": "Работа", "name_ua": "Робота", "icon": "💼", "is_active": True},
        {"_id": "service-rubric", "name_ru": "Услуги", "name_ua": "Послуги", "icon": "🛠️", "is_active": True},
    ]
    
    for rubric in super_rubrics:
        await db.super_rubrics.insert_one(rubric)
    
    # Create default cities
    cities = [
        {"_id": "moscow-city", "name_ru": "Москва", "name_ua": "Москва", "is_active": True},
        {"_id": "spb-city", "name_ru": "Санкт-Петербург", "name_ua": "Санкт-Петербург", "is_active": True},
        {"_id": "kiev-city", "name_ru": "Киев", "name_ua": "Київ", "is_active": True},
        {"_id": "kharkiv-city", "name_ru": "Харьков", "name_ua": "Харків", "is_active": True},
        {"_id": "odessa-city", "name_ru": "Одесса", "name_ua": "Одеса", "is_active": True},
        {"_id": "minsk-city", "name_ru": "Минск", "name_ua": "Мінск", "is_active": True},
    ]
    
    for city in cities:
        await db.cities.insert_one(city)
    
    # Create default packages
    packages = [
        {
            "_id": "basic-package",
            "name_ru": "Базовый",
            "name_ua": "Базовий",
            "package_type": "basic",
            "price": 0.0,
            "currency_id": "rub-id",
            "duration_days": 7,
            "features_ru": ["1 бесплатное объявление в неделю", "Стандартное размещение"],
            "features_ua": ["1 безкоштовне оголошення на тиждень", "Стандартне розміщення"],
            "is_active": True
        },
        {
            "_id": "standard-package",
            "name_ru": "Стандарт",
            "name_ua": "Стандарт",
            "package_type": "standard",
            "price": 100.0,
            "currency_id": "rub-id",
            "duration_days": 14,
            "features_ru": ["Приоритетное размещение", "Выделение цветом", "Больше просмотров"],
            "features_ua": ["Пріоритетне розміщення", "Виділення кольором", "Більше переглядів"],
            "is_active": True
        },
        {
            "_id": "premium-package",
            "name_ru": "Премиум",
            "name_ua": "Преміум",
            "package_type": "premium",
            "price": 250.0,
            "currency_id": "rub-id",
            "duration_days": 30,
            "features_ru": ["Топ размещение", "Особое выделение", "Максимум просмотров", "Поддержка"],
            "features_ua": ["Топ розміщення", "Особливе виділення", "Максимум переглядів", "Підтримка"],
            "is_active": True
        }
    ]
    
    for package in packages:
        await db.packages.insert_one(package)
    
    print("Default data initialized successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)