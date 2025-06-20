import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import database
from core.database import connect_to_mongo, close_mongo_connection

# Import routers
from api.users import router as users_router
from api.categories import router as categories_router
from api.posts import router as posts_router
from api.packages import router as packages_router

# Import services
from services.telegram_bot import webhook_handler, start_bot, stop_bot
from services.moderation import moderate_post_background

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    
    # Initialize default data
    await initialize_default_data()
    
    # Start telegram bot in background
    asyncio.create_task(start_bot())
    
    yield
    
    # Shutdown
    await stop_bot()
    await close_mongo_connection()

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
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(posts_router)
app.include_router(packages_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Telegram Marketplace API is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook endpoint"""
    return await webhook_handler(request)

@app.get("/")
async def root():
    return {"message": "Telegram Marketplace API", "docs": "/docs"}

async def initialize_default_data():
    """Initialize default categories, currencies, and packages"""
    from core.database import get_database
    
    db = await get_database()
    
    # Check if data already exists
    if await db.super_rubrics.count_documents({}) > 0:
        return
    
    # Create default currencies
    currencies = [
        {"code": "RUB", "name_ru": "Российский рубль", "name_ua": "Російський рубль", "symbol": "₽"},
        {"code": "USD", "name_ru": "Доллар США", "name_ua": "Долар США", "symbol": "$"},
        {"code": "EUR", "name_ru": "Евро", "name_ua": "Євро", "symbol": "€"},
        {"code": "UAH", "name_ru": "Украинская гривна", "name_ua": "Українська гривня", "symbol": "₴"},
    ]
    
    for currency in currencies:
        currency["is_active"] = True
        await db.currencies.insert_one(currency)
    
    # Create default super rubrics
    super_rubrics = [
        {"name_ru": "Работа", "name_ua": "Робота", "icon": "💼"},
        {"name_ru": "Услуги", "name_ua": "Послуги", "icon": "🛠️"},
    ]
    
    rubric_ids = {}
    for rubric in super_rubrics:
        rubric["is_active"] = True
        result = await db.super_rubrics.insert_one(rubric)
        rubric_ids[rubric["name_ru"]] = str(result.inserted_id)
    
    # Create default sub rubrics
    sub_rubrics = [
        # Работа
        {"name_ru": "IT и программирование", "name_ua": "IT та програмування", "super_rubric_id": rubric_ids["Работа"]},
        {"name_ru": "Дизайн", "name_ua": "Дизайн", "super_rubric_id": rubric_ids["Работа"]},
        {"name_ru": "Маркетинг", "name_ua": "Маркетинг", "super_rubric_id": rubric_ids["Работа"]},
        {"name_ru": "Продажи", "name_ua": "Продажі", "super_rubric_id": rubric_ids["Работа"]},
        
        # Услуги
        {"name_ru": "Ремонт и строительство", "name_ua": "Ремонт та будівництво", "super_rubric_id": rubric_ids["Услуги"]},
        {"name_ru": "Красота и здоровье", "name_ua": "Краса та здоров'я", "super_rubric_id": rubric_ids["Услуги"]},
        {"name_ru": "Образование", "name_ua": "Освіта", "super_rubric_id": rubric_ids["Услуги"]},
        {"name_ru": "Доставка", "name_ua": "Доставка", "super_rubric_id": rubric_ids["Услуги"]},
    ]
    
    for sub_rubric in sub_rubrics:
        sub_rubric["is_active"] = True
        await db.sub_rubrics.insert_one(sub_rubric)
    
    # Create default cities
    cities = [
        {"name_ru": "Москва", "name_ua": "Москва"},
        {"name_ru": "Санкт-Петербург", "name_ua": "Санкт-Петербург"},
        {"name_ru": "Киев", "name_ua": "Київ"},
        {"name_ru": "Харьков", "name_ua": "Харків"},
        {"name_ru": "Одесса", "name_ua": "Одеса"},
        {"name_ru": "Минск", "name_ua": "Мінск"},
    ]
    
    city_ids = {}
    for city in cities:
        city["is_active"] = True
        result = await db.cities.insert_one(city)
        city_ids[city["name_ru"]] = str(result.inserted_id)
    
    # Get RUB currency ID
    rub_currency = await db.currencies.find_one({"code": "RUB"})
    rub_id = str(rub_currency["_id"])
    
    # Create default packages
    packages = [
        {
            "name_ru": "Базовый",
            "name_ua": "Базовий",
            "package_type": "basic",
            "price": 0.0,
            "currency_id": rub_id,
            "duration_days": 7,
            "features_ru": ["1 бесплатное объявление в неделю", "Стандартное размещение"],
            "features_ua": ["1 безкоштовне оголошення на тиждень", "Стандартно розміщення"],
            "is_active": True
        },
        {
            "name_ru": "Стандарт",
            "name_ua": "Стандарт",
            "package_type": "standard",
            "price": 100.0,
            "currency_id": rub_id,
            "duration_days": 14,
            "features_ru": ["Приоритетное размещение", "Выделение цветом", "Больше просмотров"],
            "features_ua": ["Пріоритетне розміщення", "Виділення кольором", "Більше переглядів"],
            "is_active": True
        },
        {
            "name_ru": "Премиум",
            "name_ua": "Преміум",
            "package_type": "premium",
            "price": 250.0,
            "currency_id": rub_id,
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
