import sys
import os
import asyncio
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database import
from database import db

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
    query = "SELECT * FROM posts WHERE 1=1"
    params = []
    
    # Если запрашиваются посты конкретного автора, показываем все статусы
    if author_id:
        query += " AND author_id = ?"
        params.append(author_id)
    else:
        query += " AND status = ?"
        params.append(3)  # Для общего списка только активные
    
    if post_type:
        query += " AND post_type = ?"
        params.append(post_type)
    
    if super_rubric_id:
        query += " AND super_rubric_id = ?"
        params.append(super_rubric_id)
    
    if city_id:
        query += " AND city_id = ?"
        params.append(city_id)
    
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY created_at DESC LIMIT 50"
    
    results = await db.fetchall(query, params)
    return results

@posts_router.post("/jobs")
async def create_job_post(request: Request):
    """Create a job post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID", "demo-user")
    package_id = data.get("package_id")
    
    # Check if user can create free post
    if not package_id or package_id == "free-package":
        can_create_result = await check_free_post_availability(author_id)
        if not can_create_result["can_create_free"]:
            return {"error": "Free post not available yet", "next_free_at": can_create_result["next_free_at"]}
    
    # Get package details
    package = await db.fetchone("SELECT * FROM packages WHERE id = ?", [package_id]) if package_id else None
    
    # Calculate expiration date
    lifetime_days = package["post_lifetime_days"] if package else 30
    expires_at = (datetime.now() + timedelta(days=lifetime_days)).isoformat()
    
    # Add additional fields
    post_data = {
        "title": data.get("title"),
        "description": data.get("description"),
        "post_type": "job",
        "price": data.get("price"),
        "currency_id": data.get("currency_id"),
        "city_id": data.get("city_id"),
        "super_rubric_id": data.get("super_rubric_id"),
        "author_id": author_id,
        "status": 2 if package and package["price"] == 0 else 1,  # Free posts go to moderation, paid stay draft
        "package_id": package_id,
        "has_photo": package["has_photo"] if package else False,
        "has_highlight": package["has_highlight"] if package else False,
        "has_boost": package["has_boost"] if package else False,
        "post_lifetime_days": lifetime_days,
        "expires_at": expires_at,
        "views_count": 0,
        "is_premium": bool(package and package["price"] > 0),
        "ai_moderation_passed": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    post_id = await db.insert("posts", post_data)
    post_data["id"] = post_id
    
    # If free post, record usage
    if not package_id or package_id == "free-package":
        next_free_date = (datetime.now() + timedelta(days=7)).isoformat()
        free_post_data = {
            "user_id": author_id,
            "created_at": datetime.now().isoformat(),
            "next_free_post_at": next_free_date
        }
        await db.insert("user_free_posts", free_post_data)
    
    # If boost package, schedule boosts
    if package and package["has_boost"]:
        boost_data = {
            "post_id": post_id,
            "next_boost_at": (datetime.now() + timedelta(days=package["boost_interval_days"])).isoformat(),
            "boost_count": 0,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        await db.insert("post_boost_schedule", boost_data)
    
    return post_data

@posts_router.post("/services")
async def create_service_post(request: Request):
    """Create a service post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID", "demo-user")
    package_id = data.get("package_id")
    
    # Check if user can create free post
    if not package_id or package_id == "free-package":
        can_create_result = await check_free_post_availability(author_id)
        if not can_create_result["can_create_free"]:
            return {"error": "Free post not available yet", "next_free_at": can_create_result["next_free_at"]}
    
    # Get package details
    package = await db.fetchone("SELECT * FROM packages WHERE id = ?", [package_id]) if package_id else None
    
    # Calculate expiration date
    lifetime_days = package["post_lifetime_days"] if package else 30
    expires_at = (datetime.now() + timedelta(days=lifetime_days)).isoformat()
    
    # Add additional fields
    post_data = {
        "title": data.get("title"),
        "description": data.get("description"),
        "post_type": "service",
        "price": data.get("price"),
        "currency_id": data.get("currency_id"),
        "city_id": data.get("city_id"),
        "super_rubric_id": data.get("super_rubric_id"),
        "author_id": author_id,
        "status": 2 if package and package["price"] == 0 else 1,  # Free posts go to moderation, paid stay draft
        "package_id": package_id,
        "has_photo": package["has_photo"] if package else False,
        "has_highlight": package["has_highlight"] if package else False,
        "has_boost": package["has_boost"] if package else False,
        "post_lifetime_days": lifetime_days,
        "expires_at": expires_at,
        "views_count": 0,
        "is_premium": bool(package and package["price"] > 0),
        "ai_moderation_passed": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    post_id = await db.insert("posts", post_data)
    post_data["id"] = post_id
    
    # If free post, record usage
    if not package_id or package_id == "free-package":
        next_free_date = (datetime.now() + timedelta(days=7)).isoformat()
        free_post_data = {
            "user_id": author_id,
            "created_at": datetime.now().isoformat(),
            "next_free_post_at": next_free_date
        }
        await db.insert("user_free_posts", free_post_data)
    
    # If boost package, schedule boosts
    if package and package["has_boost"]:
        boost_data = {
            "post_id": post_id,
            "next_boost_at": (datetime.now() + timedelta(days=package["boost_interval_days"])).isoformat(),
            "boost_count": 0,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        await db.insert("post_boost_schedule", boost_data)
    
    return post_data

@posts_router.put("/{post_id}/status")
async def update_post_status(post_id: str, request: Request):
    """Update post status"""
    data = await request.json()
    status = data.get("status", 3)
    
    update_data = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    
    rows_affected = await db.update("posts", update_data, "id = ?", [post_id])
    
    if rows_affected == 0:
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
    existing = await db.fetchone("SELECT id FROM favorites WHERE user_id = ? AND post_id = ?", [user_id, post_id])
    if existing:
        return {"error": "Already in favorites"}
    
    favorite_data = {
        "user_id": user_id, 
        "post_id": post_id,
        "created_at": datetime.now().isoformat()
    }
    
    await db.insert("favorites", favorite_data)
    return {"message": "Added to favorites"}

@posts_router.delete("/favorites")
async def remove_from_favorites(request: Request):
    """Remove post from favorites"""
    data = await request.json()
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    
    if not user_id or not post_id:
        return {"error": "user_id and post_id are required"}
    
    rows_affected = await db.delete("favorites", "user_id = ? AND post_id = ?", [user_id, post_id])
    
    if rows_affected == 0:
        return {"error": "Not in favorites"}
    
    return {"message": "Removed from favorites"}

@posts_router.get("/favorites/{user_id}")
async def get_user_favorites(user_id: str):
    """Get user's favorite posts"""
    query = """
        SELECT p.* FROM posts p 
        INNER JOIN favorites f ON p.id = f.post_id 
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """
    
    results = await db.fetchall(query, [user_id])
    return results

@posts_router.get("/{post_id}")
async def get_post_details(post_id: str, user_id: str = None):
    """Get post details and increment views if not viewed by this user"""
    post = await db.fetchone("SELECT * FROM posts WHERE id = ?", [post_id])
    
    if not post:
        return {"error": "Post not found"}
    
    # Increment views only if user hasn't viewed this post before
    if user_id:
        existing_view = await db.fetchone(
            "SELECT id FROM post_views WHERE post_id = ? AND user_id = ?", 
            [post_id, user_id]
        )
        
        if not existing_view:
            # Increment views count
            await db.update("posts", {"views_count": post["views_count"] + 1}, "id = ?", [post_id])
            
            # Record that this user viewed this post
            view_data = {
                "post_id": post_id,
                "user_id": user_id,
                "viewed_at": datetime.now().isoformat()
            }
            await db.insert("post_views", view_data)
            
            post["views_count"] = post["views_count"] + 1
    
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
    settings = await db.fetchone("SELECT * FROM app_settings WHERE id = ?", ["default"])
    
    if not settings:
        # Return default settings if none exist
        settings = {
            "show_view_counts": True,
            "telegram_bot_token": "***hidden***",
            "mistral_api_key": "***hidden***",
            "app_name": "Telegram Marketplace",
            "app_description": "Платформа частных объявлений",
            "free_posts_per_week": 1,
            "moderation_enabled": True,
            "id": "default"
        }
    else:
        # Hide sensitive fields
        settings["telegram_bot_token"] = "***hidden***"
        settings["mistral_api_key"] = "***hidden***"
    
    return settings

@admin_router.put("/settings")
async def update_app_settings(request: Request):
    """Update application settings"""
    data = await request.json()
    
    # Remove sensitive fields for logging
    safe_data = {k: v for k, v in data.items() if k not in ["telegram_bot_token", "mistral_api_key"]}
    print(f"Updating settings: {safe_data}")
    
    # Check if settings exist
    existing = await db.fetchone("SELECT id FROM app_settings WHERE id = ?", ["default"])
    
    if existing:
        rows_affected = await db.update("app_settings", data, "id = ?", ["default"])
    else:
        data["id"] = "default"
        await db.insert("app_settings", data)
    
    return {"success": True, "message": "Settings updated"}

# Statistics endpoints
@admin_router.get("/stats/users")
async def get_user_stats():
    """Get user statistics"""
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # Total users
    total_users_result = await db.fetchone("SELECT COUNT(*) as count FROM users")
    total_users = total_users_result["count"] if total_users_result else 0
    
    # New users last 7 days
    new_users_7d_result = await db.fetchone(
        "SELECT COUNT(*) as count FROM users WHERE created_at >= ?", 
        [last_7_days.isoformat()]
    )
    new_users_7d = new_users_7d_result["count"] if new_users_7d_result else 0
    
    # New users last 30 days
    new_users_30d_result = await db.fetchone(
        "SELECT COUNT(*) as count FROM users WHERE created_at >= ?", 
        [last_30_days.isoformat()]
    )
    new_users_30d = new_users_30d_result["count"] if new_users_30d_result else 0
    
    # Daily new users for chart (last 7 days)
    daily_users = []
    for i in range(7):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count_result = await db.fetchone(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= ? AND created_at < ?",
            [day_start.isoformat(), day_end.isoformat()]
        )
        count = count_result["count"] if count_result else 0
        
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
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # Total posts
    total_posts_result = await db.fetchone("SELECT COUNT(*) as count FROM posts")
    total_posts = total_posts_result["count"] if total_posts_result else 0
    
    # Active posts
    active_posts_result = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE status = 3")
    active_posts = active_posts_result["count"] if active_posts_result else 0
    
    # New posts last 7 days
    new_posts_7d_result = await db.fetchone(
        "SELECT COUNT(*) as count FROM posts WHERE created_at >= ?", 
        [last_7_days.isoformat()]
    )
    new_posts_7d = new_posts_7d_result["count"] if new_posts_7d_result else 0
    
    # New posts last 30 days
    new_posts_30d_result = await db.fetchone(
        "SELECT COUNT(*) as count FROM posts WHERE created_at >= ?", 
        [last_30_days.isoformat()]
    )
    new_posts_30d = new_posts_30d_result["count"] if new_posts_30d_result else 0
    
    # Most popular posts (by views)
    popular_posts = await db.fetchall(
        """SELECT p.id, p.title, p.views_count, p.author_id,
           (SELECT COUNT(*) FROM favorites f WHERE f.post_id = p.id) as favorites_count
           FROM posts p 
           WHERE p.status = 3 
           ORDER BY p.views_count DESC 
           LIMIT 10"""
    )
    
    # Posts by type
    job_posts_result = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE post_type = 'job'")
    job_posts = job_posts_result["count"] if job_posts_result else 0
    
    service_posts_result = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE post_type = 'service'")
    service_posts = service_posts_result["count"] if service_posts_result else 0
    
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
    results = await db.fetchall("SELECT * FROM currencies ORDER BY created_at DESC")
    return results

@admin_router.post("/currencies")
async def admin_create_currency(request: Request):
    """Create currency"""
    data = await request.json()
    
    currency_data = {
        "code": data.get("code"),
        "name_ru": data.get("name_ru"),
        "name_ua": data.get("name_ua"),
        "symbol": data.get("symbol"),
        "is_active": data.get("is_active", True),
        "created_at": datetime.now().isoformat()
    }
    
    currency_id = await db.insert("currencies", currency_data)
    currency_data["id"] = currency_id
    
    return currency_data

@admin_router.put("/currencies/{currency_id}")
async def admin_update_currency(currency_id: str, request: Request):
    """Update currency"""
    data = await request.json()
    
    rows_affected = await db.update("currencies", data, "id = ?", [currency_id])
    
    if rows_affected == 0:
        return {"error": "Currency not found"}
    
    return {"success": True, "message": "Currency updated"}

@admin_router.delete("/currencies/{currency_id}")
async def admin_delete_currency(currency_id: str):
    """Delete currency"""
    rows_affected = await db.delete("currencies", "id = ?", [currency_id])
    
    if rows_affected == 0:
        return {"error": "Currency not found"}
    
    return {"success": True, "message": "Currency deleted"}

# Packages router
packages_router = APIRouter(prefix="/api/packages", tags=["packages"])

@packages_router.get("/")
async def get_active_packages():
    """Get all active packages for users"""
    results = await db.fetchall(
        "SELECT * FROM packages WHERE is_active = 1 ORDER BY sort_order ASC"
    )
    
    # Parse features from JSON strings
    for package in results:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return results

@packages_router.get("/check-free-post/{user_id}")
async def check_free_post_availability(user_id: str):
    """Check if user can create free post"""
    now = datetime.now()
    
    # Check user's last free post
    last_free = await db.fetchone(
        "SELECT * FROM user_free_posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        [user_id]
    )
    
    if not last_free:
        return {"can_create_free": True, "next_free_at": None}
    
    next_free_at = datetime.fromisoformat(last_free["next_free_post_at"])
    can_create = now >= next_free_at
    
    return {
        "can_create_free": can_create,
        "next_free_at": last_free["next_free_post_at"] if not can_create else None
    }

@packages_router.post("/purchase")
async def purchase_package(request: Request):
    """Purchase a package (initiate Telegram payment)"""
    data = await request.json()
    user_id = data.get("user_id")
    package_id = data.get("package_id")
    
    if not user_id or not package_id:
        return {"error": "user_id and package_id are required"}
    
    # Get package details
    package = await db.fetchone("SELECT * FROM packages WHERE id = ?", [package_id])
    if not package:
        return {"error": "Package not found"}
    
    if package["price"] == 0:
        return {"error": "Free package cannot be purchased"}
    
    # Create pending purchase record
    purchase_data = {
        "user_id": user_id,
        "package_id": package_id,
        "purchased_at": datetime.now().isoformat(),
        "payment_status": "pending",
        "amount": package["price"],
        "currency_code": "RUB",  # Will get from currency table
        "created_at": datetime.now().isoformat()
    }
    
    purchase_id = await db.insert("user_packages", purchase_data)
    
    # Here would be Telegram Payment API integration
    # For now, return payment info
    return {
        "purchase_id": purchase_id,
        "amount": package["price"],
        "currency": "RUB",
        "description": f"Тариф: {package['name_ru']}",
        "telegram_payment_url": f"tg://payment?purchase_id={purchase_id}"
    }
users_router = APIRouter(prefix="/api/users", tags=["users"])

@users_router.post("/")
async def create_user(request: Request):
    """Create a new user"""
    data = await request.json()
    
    # Check if user already exists by telegram_id
    existing_user = await db.fetchone("SELECT * FROM users WHERE telegram_id = ?", [data.get("telegram_id")])
    if existing_user:
        return existing_user
    
    # Add default fields
    user_data = {
        "telegram_id": data.get("telegram_id"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "username": data.get("username"),
        "language": data.get("language", "ru"),
        "theme": data.get("theme", "light"),
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    user_id = await db.insert("users", user_data)
    user_data["id"] = user_id
    
    return user_data

@users_router.get("/{user_id}")
async def get_user(user_id: str):
    user = await db.fetchone("SELECT * FROM users WHERE id = ?", [user_id])
    
    if user:
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
    
    rows_affected = await db.update("users", update_data, "id = ?", [user_id])
    
    if rows_affected == 0:
        return {"error": "User not found"}
    
    updated_user = await db.fetchone("SELECT * FROM users WHERE id = ?", [user_id])
    return updated_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize database
    await db.init_db()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)