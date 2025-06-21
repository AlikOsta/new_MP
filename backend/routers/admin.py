"""
Admin router - handles administrative operations
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from database import db
from datetime import datetime
from services.stats_service import StatsService
from background_tasks import manual_expire_posts, manual_boost_posts
from config import ADMIN_USERNAME, ADMIN_PASSWORD
import base64

router = APIRouter(prefix="/api/admin", tags=["admin"])

def check_admin_auth(request: Request):
    """Check admin authentication using environment variables"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Decode base64 credentials
        encoded_credentials = auth_header.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)
        
        # Check against environment variables
        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication format")

# Dashboard endpoints
@router.get("/stats", dependencies=[Depends(check_admin_auth)])
async def get_admin_statistics():
    """Get comprehensive admin statistics"""
    return await StatsService.get_admin_stats()

@router.get("/moderation-stats", dependencies=[Depends(check_admin_auth)])
async def get_moderation_statistics():
    """Get moderation statistics"""
    return await StatsService.get_moderation_stats()

# CRUD endpoints for posts
@router.get("/posts", dependencies=[Depends(check_admin_auth)])
async def admin_get_posts(page: int = 1, limit: int = 50, status: int = None):
    """Get all posts for admin with optional status filter"""
    offset = (page - 1) * limit
    
    query = "SELECT * FROM posts"
    params = []
    
    if status is not None:
        query += " WHERE status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    posts = await db.fetchall(query, params)
    
    # Get total count
    count_query = "SELECT COUNT(*) as total FROM posts"
    count_params = []
    if status is not None:
        count_query += " WHERE status = ?"
        count_params.append(status)
    
    total_result = await db.fetchone(count_query, count_params)
    
    return {
        "posts": posts,
        "total": total_result["total"] if total_result else 0,
        "page": page,
        "limit": limit
    }

@router.put("/posts/{post_id}", dependencies=[Depends(check_admin_auth)])
async def admin_update_post(post_id: str, request: Request):
    """Update post (admin only)"""
    data = await request.json()
    data["updated_at"] = datetime.now().isoformat()
    
    rows_affected = await db.update("posts", data, "id = ?", [post_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"success": True, "message": "Post updated"}

@router.delete("/posts/{post_id}", dependencies=[Depends(check_admin_auth)])
async def admin_delete_post(post_id: str):
    """Delete post (admin only)"""
    rows_affected = await db.delete("posts", "id = ?", [post_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"success": True, "message": "Post deleted"}

# CRUD endpoints for packages
@router.get("/packages", dependencies=[Depends(check_admin_auth)])
async def admin_get_packages():
    """Get all packages for admin"""
    results = await db.fetchall("SELECT * FROM packages ORDER BY sort_order ASC")
    
    # Parse features from pipe-separated strings
    for package in results:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return results

@router.post("/packages", dependencies=[Depends(check_admin_auth)])
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

@router.put("/packages/{package_id}", dependencies=[Depends(check_admin_auth)])
async def admin_update_package(package_id: str, request: Request):
    """Update package"""
    data = await request.json()
    
    # Convert features arrays to strings
    if "features_ru" in data and isinstance(data["features_ru"], list):
        data["features_ru"] = "|".join(data["features_ru"])
    if "features_ua" in data and isinstance(data["features_ua"], list):
        data["features_ua"] = "|".join(data["features_ua"])
    
    data["updated_at"] = datetime.now().isoformat()
    
    rows_affected = await db.update("packages", data, "id = ?", [package_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {"success": True, "message": "Package updated"}

@router.delete("/packages/{package_id}", dependencies=[Depends(check_admin_auth)])
async def admin_delete_package(package_id: str):
    """Delete package"""
    rows_affected = await db.delete("packages", "id = ?", [package_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {"success": True, "message": "Package deleted"}

# CRUD endpoints for categories (super rubrics)
@router.get("/categories", dependencies=[Depends(check_admin_auth)])
async def admin_get_categories():
    """Get all categories for admin"""
    results = await db.fetchall("SELECT * FROM super_rubrics ORDER BY name_ru ASC")
    return results

@router.post("/categories", dependencies=[Depends(check_admin_auth)])
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

@router.put("/categories/{category_id}", dependencies=[Depends(check_admin_auth)])
async def admin_update_category(category_id: str, request: Request):
    """Update category"""
    data = await request.json()
    
    rows_affected = await db.update("super_rubrics", data, "id = ?", [category_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"success": True, "message": "Category updated"}

@router.delete("/categories/{category_id}", dependencies=[Depends(check_admin_auth)])
async def admin_delete_category(category_id: str):
    """Delete category"""
    # Check if category is used in posts
    posts_count = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE super_rubric_id = ?", [category_id])
    
    if posts_count and posts_count["count"] > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete category. It's used in {posts_count['count']} posts")
    
    rows_affected = await db.delete("super_rubrics", "id = ?", [category_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"success": True, "message": "Category deleted"}

# CRUD endpoints for cities
@router.get("/cities", dependencies=[Depends(check_admin_auth)])
async def admin_get_cities():
    """Get all cities for admin"""
    results = await db.fetchall("SELECT * FROM cities ORDER BY name_ru ASC")
    return results

@router.post("/cities", dependencies=[Depends(check_admin_auth)])
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

@router.put("/cities/{city_id}", dependencies=[Depends(check_admin_auth)])
async def admin_update_city(city_id: str, request: Request):
    """Update city"""
    data = await request.json()
    
    rows_affected = await db.update("cities", data, "id = ?", [city_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="City not found")
    
    return {"success": True, "message": "City updated"}

@router.delete("/cities/{city_id}", dependencies=[Depends(check_admin_auth)])
async def admin_delete_city(city_id: str):
    """Delete city"""
    # Check if city is used in posts
    posts_count = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE city_id = ?", [city_id])
    
    if posts_count and posts_count["count"] > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete city. It's used in {posts_count['count']} posts")
    
    rows_affected = await db.delete("cities", "id = ?", [city_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="City not found")
    
    return {"success": True, "message": "City deleted"}

# Background tasks management endpoints
@router.post("/tasks/expire-posts", dependencies=[Depends(check_admin_auth)])
async def admin_expire_posts():
    """Manually expire old posts"""
    result = await manual_expire_posts()
    return result

@router.post("/tasks/boost-posts", dependencies=[Depends(check_admin_auth)])
async def admin_boost_posts():
    """Manually boost posts"""
    result = await manual_boost_posts()
    return result

@router.get("/tasks/status", dependencies=[Depends(check_admin_auth)])
async def admin_tasks_status():
    """Get background tasks status"""
    return await StatsService.get_moderation_stats()