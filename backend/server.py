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
    cursor = db.super_rubrics.find({"is_active": True})
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

@categories_router.get("/cities")
async def get_cities():
    cursor = db.cities.find({"is_active": True})
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

@categories_router.get("/currencies")
async def get_currencies():
    cursor = db.currencies.find({"is_active": True})
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

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

# Packages router  
packages_router = APIRouter(prefix="/api/packages", tags=["packages"])

@packages_router.get("/")
async def get_packages():
    cursor = db.packages.find({"is_active": True})
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        result.append(doc)
    return result

# Users router
users_router = APIRouter(prefix="/api/users", tags=["users"])

@users_router.get("/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if user:
        user["id"] = str(user["_id"])
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
    # Shutdown
    client.close()

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
app.include_router(packages_router)
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
