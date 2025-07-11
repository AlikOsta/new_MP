import sys
import os
import asyncio
import uuid
import httpx
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

# AI Moderation import
from ai_moderation import init_moderation_services, moderate_post_content, mistral_moderator, telegram_notifier

# Background tasks import
from background_tasks import start_background_tasks, stop_background_tasks, manual_expire_posts, manual_boost_posts

# Import API routers with simple approach
from fastapi import APIRouter

# Categories router
categories_router = APIRouter(prefix="/api/categories", tags=["categories"])

@categories_router.get("/super-rubrics")
async def get_super_rubrics():
    results = await db.fetchall("SELECT id, name_ru, name_ua, icon FROM super_rubrics WHERE is_active = 1")
    return results

@categories_router.get("/cities")
async def get_cities():
    results = await db.fetchall("SELECT id, name_ru, name_ua FROM cities WHERE is_active = 1")
    return results

@categories_router.get("/currencies")
async def get_currencies():
    results = await db.fetchall("SELECT id, code, name_ru, name_ua, symbol FROM currencies WHERE is_active = 1")
    return results

@categories_router.get("/all")
async def get_all_reference_data():
    """Get all reference data in one request for Telegram Mini App optimization"""
    super_rubrics = await db.fetchall("SELECT id, name_ru, name_ua, icon FROM super_rubrics WHERE is_active = 1")
    cities = await db.fetchall("SELECT id, name_ru, name_ua FROM cities WHERE is_active = 1")
    currencies = await db.fetchall("SELECT id, code, name_ru, name_ua, symbol FROM currencies WHERE is_active = 1")
    packages = await db.fetchall("""
        SELECT id, name_ru, name_ua, package_type, price, currency_id, 
               duration_days, post_lifetime_days, features_ru, features_ua,
               has_photo, has_highlight, has_boost, sort_order
        FROM packages WHERE is_active = 1 ORDER BY sort_order ASC
    """)
    
    # Parse features from pipe-separated strings
    for package in packages:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return {
        "categories": super_rubrics,
        "cities": cities,
        "currencies": currencies,
        "packages": packages
    }

# Posts router
posts_router = APIRouter(prefix="/api/posts", tags=["posts"])

@posts_router.get("/")
async def get_posts(
    post_type: str = None, 
    search: str = None, 
    author_id: str = None,
    super_rubric_id: str = None,
    city_id: str = None,
    page: int = 1,
    limit: int = 20
):
    # Validation and limits for Telegram Mini App
    if limit > 50:
        limit = 50  # Maximum 50 posts per request
    if page < 1:
        page = 1
    
    offset = (page - 1) * limit
    
    # Optimized query with selective fields
    query = """SELECT id, title, description, post_type, price, currency_id, city_id, 
                      super_rubric_id, author_id, status, has_photo, has_highlight, 
                      has_boost, views_count, created_at, expires_at 
               FROM posts WHERE 1=1"""
    params = []
    
    # Efficient filtering with indexed columns first
    if author_id:
        query += " AND author_id = ?"
        params.append(author_id)
    else:
        query += " AND status = ?"
        params.append(3)  # Only active posts for public list
    
    if post_type:
        query += " AND post_type = ?"
        params.append(post_type)
    
    if super_rubric_id:
        query += " AND super_rubric_id = ?"
        params.append(super_rubric_id)
    
    if city_id:
        query += " AND city_id = ?"
        params.append(city_id)
    
    # Search is expensive, so it comes last
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    # Order by created_at DESC (indexed) and add pagination
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    results = await db.fetchall(query, params)
    
    # Return with metadata for pagination
    return {
        "posts": results,
        "page": page,
        "limit": limit,
        "has_more": len(results) == limit
    }

@posts_router.post("/jobs")
async def create_job_post(request: Request):
    """Create a job post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID")
    if not author_id:
        return {"error": "Authentication required"}
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
    
    # Start AI moderation process
    try:
        moderation_result = await moderate_post_content(post_data)
        
        # Log AI moderation result
        if moderation_result.get("ai_result"):
            ai_log_data = {
                "post_id": post_id,
                "ai_decision": moderation_result["ai_result"]["decision"],
                "ai_confidence": moderation_result["ai_result"]["confidence"],
                "ai_reason": moderation_result["ai_result"]["reason"],
                "moderated_at": datetime.now().isoformat()
            }
            await db.insert("ai_moderation_log", ai_log_data)
        
        # Update post status based on moderation result
        final_status = moderation_result.get("final_status", 3)
        await db.update("posts", {
            "status": final_status,
            "ai_moderation_passed": moderation_result["decision"] != "rejected"
        }, "id = ?", [post_id])
        
        # Send notification to moderator if needed
        if moderation_result.get("should_notify_moderator") and telegram_notifier:
            await telegram_notifier.send_moderation_request(post_data, moderation_result.get("ai_result"))
        
        # Update post_data with final status for response
        post_data["status"] = final_status
        post_data["ai_moderation_passed"] = moderation_result["decision"] != "rejected"
        
    except Exception as e:
        print(f"Error in moderation process: {str(e)}")
        # If moderation fails, set status to manual review
        await db.update("posts", {"status": 3}, "id = ?", [post_id])
        post_data["status"] = 3
    
    return post_data

@posts_router.post("/services")
async def create_service_post(request: Request):
    """Create a service post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID")
    if not author_id:
        return {"error": "Authentication required"}
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
    
    # Start AI moderation process
    try:
        moderation_result = await moderate_post_content(post_data)
        
        # Log AI moderation result
        if moderation_result.get("ai_result"):
            ai_log_data = {
                "post_id": post_id,
                "ai_decision": moderation_result["ai_result"]["decision"],
                "ai_confidence": moderation_result["ai_result"]["confidence"],
                "ai_reason": moderation_result["ai_result"]["reason"],
                "moderated_at": datetime.now().isoformat()
            }
            await db.insert("ai_moderation_log", ai_log_data)
        
        # Update post status based on moderation result
        final_status = moderation_result.get("final_status", 3)
        await db.update("posts", {
            "status": final_status,
            "ai_moderation_passed": moderation_result["decision"] != "rejected"
        }, "id = ?", [post_id])
        
        # Send notification to moderator if needed
        if moderation_result.get("should_notify_moderator") and telegram_notifier:
            await telegram_notifier.send_moderation_request(post_data, moderation_result.get("ai_result"))
        
        # Update post_data with final status for response
        post_data["status"] = final_status
        post_data["ai_moderation_passed"] = moderation_result["decision"] != "rejected"
        
    except Exception as e:
        print(f"Error in moderation process: {str(e)}")
        # If moderation fails, set status to manual review
        await db.update("posts", {"status": 3}, "id = ?", [post_id])
        post_data["status"] = 3
    
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
# TODO: Replace with proper authentication system
ADMIN_CREDENTIALS = {
    "username": os.environ.get("ADMIN_USERNAME", "admin"),
    "password": os.environ.get("ADMIN_PASSWORD", "admin123")  # In production, use hashed passwords
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
            "telegram_payment_token": "***hidden***",
            "telegram_moderator_chat_id": "",
            "telegram_moderator_username": "",
            "mistral_api_key": "***hidden***",
            "app_name": "Telegram Marketplace",
            "app_description": "Платформа частных объявлений",
            "free_posts_per_week": 1,
            "moderation_enabled": True,
            "ai_moderation_enabled": True,
            "post_lifetime_days": 30,
            "id": "default"
        }
    else:
        # Hide sensitive fields
        settings["telegram_bot_token"] = "***hidden***"
        settings["telegram_payment_token"] = "***hidden***"
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

# CRUD endpoints for packages (тарифы)
@admin_router.get("/packages")
async def admin_get_packages():
    """Get all packages for admin"""
    results = await db.fetchall("SELECT * FROM packages ORDER BY sort_order ASC")
    
    # Parse features from JSON strings
    for package in results:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return results

@admin_router.post("/packages")
async def admin_create_package(request: Request):
    """Create package"""
    data = await request.json()
    
    package_data = {
        "name_ru": data.get("name_ru"),
        "name_ua": data.get("name_ua"),
        "package_type": data.get("package_type"),
        "price": data.get("price", 0),
        "currency_id": data.get("currency_id"),
        "duration_days": data.get("duration_days", 30),
        "post_lifetime_days": data.get("post_lifetime_days", 30),
        "features_ru": "|".join(data.get("features_ru", [])),
        "features_ua": "|".join(data.get("features_ua", [])),
        "has_photo": data.get("has_photo", False),
        "has_highlight": data.get("has_highlight", False),
        "has_boost": data.get("has_boost", False),
        "boost_interval_days": data.get("boost_interval_days"),
        "is_active": data.get("is_active", True),
        "sort_order": data.get("sort_order", 0),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    package_id = await db.insert("packages", package_data)
    package_data["id"] = package_id
    
    return package_data

@admin_router.put("/packages/{package_id}")
async def admin_update_package(package_id: str, request: Request):
    """Update package"""
    data = await request.json()
    
    # Convert features arrays to strings
    if "features_ru" in data and isinstance(data["features_ru"], list):
        data["features_ru"] = "|".join(data["features_ru"])
    if "features_ua" in data and isinstance(data["features_ua"], list):
        data["features_ua"] = "|".join(data["features_ua"])
    
    rows_affected = await db.update("packages", data, "id = ?", [package_id])
    
    if rows_affected == 0:
        return {"error": "Package not found"}
    
    return {"success": True, "message": "Package updated"}

@admin_router.delete("/packages/{package_id}")
async def admin_delete_package(package_id: str):
    """Delete package"""
    rows_affected = await db.delete("packages", "id = ?", [package_id])
    
    if rows_affected == 0:
        return {"error": "Package not found"}
    
    return {"success": True, "message": "Package deleted"}

# CRUD endpoints for categories (super rubrics)
@admin_router.get("/categories")
async def admin_get_categories():
    """Get all categories for admin"""
    results = await db.fetchall("SELECT * FROM super_rubrics ORDER BY name_ru ASC")
    return results

@admin_router.post("/categories")
async def admin_create_category(request: Request):
    """Create category"""
    data = await request.json()
    
    category_data = {
        "name_ru": data.get("name_ru"),
        "name_ua": data.get("name_ua"),
        "icon": data.get("icon"),
        "is_active": data.get("is_active", True)
    }
    
    category_id = await db.insert("super_rubrics", category_data)
    category_data["id"] = category_id
    
    return category_data

@admin_router.put("/categories/{category_id}")
async def admin_update_category(category_id: str, request: Request):
    """Update category"""
    data = await request.json()
    
    rows_affected = await db.update("super_rubrics", data, "id = ?", [category_id])
    
    if rows_affected == 0:
        return {"error": "Category not found"}
    
    return {"success": True, "message": "Category updated"}

@admin_router.delete("/categories/{category_id}")
async def admin_delete_category(category_id: str):
    """Delete category"""
    # Check if category is used in posts
    posts_count = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE super_rubric_id = ?", [category_id])
    
    if posts_count and posts_count["count"] > 0:
        return {"error": f"Cannot delete category. It's used in {posts_count['count']} posts"}
    
    rows_affected = await db.delete("super_rubrics", "id = ?", [category_id])
    
    if rows_affected == 0:
        return {"error": "Category not found"}
    
    return {"success": True, "message": "Category deleted"}

# CRUD endpoints for cities
@admin_router.get("/cities")
async def admin_get_cities():
    """Get all cities for admin"""
    results = await db.fetchall("SELECT * FROM cities ORDER BY name_ru ASC")
    return results

@admin_router.post("/cities")
async def admin_create_city(request: Request):
    """Create city"""
    data = await request.json()
    
    city_data = {
        "name_ru": data.get("name_ru"),
        "name_ua": data.get("name_ua"),
        "is_active": data.get("is_active", True)
    }
    
    city_id = await db.insert("cities", city_data)
    city_data["id"] = city_id
    
    return city_data

@admin_router.put("/cities/{city_id}")
async def admin_update_city(city_id: str, request: Request):
    """Update city"""
    data = await request.json()
    
    rows_affected = await db.update("cities", data, "id = ?", [city_id])
    
    if rows_affected == 0:
        return {"error": "City not found"}
    
    return {"success": True, "message": "City updated"}

@admin_router.delete("/cities/{city_id}")
async def admin_delete_city(city_id: str):
    """Delete city"""
    # Check if city is used in posts
    posts_count = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE city_id = ?", [city_id])
    
    if posts_count and posts_count["count"] > 0:
        return {"error": f"Cannot delete city. It's used in {posts_count['count']} posts"}
    
    rows_affected = await db.delete("cities", "id = ?", [city_id])
    
    if rows_affected == 0:
        return {"error": "City not found"}
    
    return {"success": True, "message": "City deleted"}

# Background tasks management endpoints
@admin_router.post("/tasks/expire-posts")
async def admin_expire_posts():
    """Manually expire old posts"""
    result = await manual_expire_posts()
    return result

@admin_router.post("/tasks/boost-posts") 
async def admin_boost_posts():
    """Manually boost posts"""
    result = await manual_boost_posts()
    return result

@admin_router.get("/tasks/status")
async def admin_tasks_status():
    """Get background tasks status"""
    from background_tasks import background_tasks
    
    # Get some statistics
    now = datetime.now().isoformat()
    
    # Posts ready to expire
    expire_ready = await db.fetchall(
        "SELECT COUNT(*) as count FROM posts WHERE expires_at < ? AND status = 4",
        [now]
    )
    
    # Posts ready to boost
    boost_ready = await db.fetchall(
        """SELECT COUNT(*) as count FROM post_boost_schedule pbs
           JOIN posts p ON pbs.post_id = p.id
           WHERE pbs.next_boost_at <= ? AND pbs.is_active = 1 AND p.status = 4""",
        [now]
    )
    
    return {
        "background_tasks_running": background_tasks.is_running,
        "posts_ready_to_expire": expire_ready[0]["count"] if expire_ready else 0,
        "posts_ready_to_boost": boost_ready[0]["count"] if boost_ready else 0,
        "current_time": now
    }

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
    # Startup - Initialize database and services
    await db.init_db()
    await init_moderation_services()
    
    # Start background tasks
    asyncio.create_task(start_background_tasks())
    print("🚀 Background tasks started")
    
    yield
    
    # Shutdown - Stop background tasks
    await stop_background_tasks()
    print("🛑 Background tasks stopped")

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

# Import function from packages_router  
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
app.include_router(categories_router)
app.include_router(packages_router)
app.include_router(posts_router)
app.include_router(admin_router)
app.include_router(users_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Telegram Marketplace API is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook endpoint"""
    try:
        update = await request.json()
        
        # Обработка callback query (нажатие кнопок модератора)
        if "callback_query" in update:
            callback = update["callback_query"]
            callback_data = callback.get("data", "")
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            
            # Извлекаем действие и ID поста
            if "_" in callback_data:
                action, post_id = callback_data.split("_", 1)
                
                if action in ["approve", "reject"]:
                    await handle_moderation_decision(action, post_id, callback["from"])
                    
                    # Обновляем сообщение в Telegram
                    await update_telegram_message(chat_id, message_id, action, post_id)
        
        return {"ok": True}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {"ok": True}  # Всегда возвращаем success для Telegram

async def handle_moderation_decision(action: str, post_id: str, moderator_info: dict):
    """Обработка решения модератора"""
    try:
        # Получаем пост
        post = await db.fetchone("SELECT * FROM posts WHERE id = ?", [post_id])
        if not post:
            print(f"Post {post_id} not found")
            return
        
        # Определяем новый статус
        new_status = 4 if action == "approve" else 5  # Опубликовано или Заблокировано
        
        # Обновляем пост
        await db.update("posts", {
            "status": new_status,
            "updated_at": datetime.now().isoformat()
        }, "id = ?", [post_id])
        
        # Если пост был платным и отклонен - возвращаем деньги
        if action == "reject" and post.get("is_premium"):
            await handle_refund(post_id, post.get("author_id"))
        
        # Отправляем уведомление об изменении статуса
        if telegram_notifier:
            status_text = "approved" if action == "approve" else "rejected"
            moderator_username = moderator_info.get("username", "неизвестен")
            await telegram_notifier.send_status_update(dict(post), status_text, moderator_username)
        
        print(f"Post {post_id} {action}ed by moderator {moderator_info.get('username', 'unknown')}")
        
    except Exception as e:
        print(f"Error handling moderation decision: {str(e)}")

async def update_telegram_message(chat_id: str, message_id: int, action: str, post_id: str):
    """Обновляет сообщение в Telegram после принятия решения"""
    if not telegram_notifier:
        return
    
    try:
        action_text = "✅ ОПУБЛИКОВАНО" if action == "approve" else "❌ ОТКЛОНЕНО"
        new_text = f"{action_text}\n\nОбъявление {post_id} обработано."
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{telegram_notifier.base_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": new_text,
                    "parse_mode": "HTML"
                }
            )
    except Exception as e:
        print(f"Error updating Telegram message: {str(e)}")

async def handle_refund(post_id: str, author_id: str):
    """Обработка возврата денег за отклоненный платный пост"""
    try:
        # Находим покупку пакета для этого поста
        purchase = await db.fetchone(
            "SELECT * FROM user_packages WHERE post_id = ? AND payment_status = 'paid'", 
            [post_id]
        )
        
        if purchase:
            # Помечаем как возвращенный
            await db.update("user_packages", {
                "payment_status": "refunded"
            }, "id = ?", [purchase["id"]])
            
            print(f"Refund processed for post {post_id}, user {author_id}, amount {purchase.get('amount', 0)}")
            
            # Здесь можно добавить интеграцию с реальной платежной системой для возврата
            
    except Exception as e:
        print(f"Error processing refund: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Telegram Marketplace API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)