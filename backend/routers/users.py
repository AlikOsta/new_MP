"""
Users router - handles user operations
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from datetime import datetime
from services.post_service import PostService
from services.stats_service import StatsService

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/")
async def create_or_update_user(request: Request):
    """Create or update user from Telegram data"""
    data = await request.json()
    
    telegram_id = data.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")
    
    # Check if user exists
    existing_user = await db.fetchone("SELECT * FROM users WHERE telegram_id = ?", [telegram_id])
    
    user_data = {
        "telegram_id": telegram_id,
        "username": data.get("username"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "language_code": data.get("language_code", "ru"),
        "updated_at": datetime.now().isoformat()
    }
    
    if existing_user:
        # Update existing user
        await db.update("users", user_data, "telegram_id = ?", [telegram_id])
        user_data["id"] = existing_user["id"]
        user_data["created_at"] = existing_user["created_at"]
    else:
        # Create new user
        user_data["created_at"] = datetime.now().isoformat()
        user_data["is_active"] = True
        user_id = await db.insert("users", user_data)
        user_data["id"] = user_id
    
    return user_data

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID"""
    user = await db.fetchone("SELECT * FROM users WHERE id = ?", [user_id])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/{user_id}/posts")
async def get_user_posts(user_id: str, page: int = 1, limit: int = 20):
    """Get posts by user"""
    filters = {
        "author_id": user_id,
        "page": page,
        "limit": limit
    }
    
    return await PostService.get_posts_with_filters(filters)

@router.get("/{user_id}/stats")
async def get_user_statistics(user_id: str):
    """Get user statistics"""
    return await StatsService.get_user_stats(user_id)

@router.get("/{user_id}/free-post-status")
async def get_free_post_status(user_id: str):
    """Check if user can create a free post"""
    return await PostService.check_free_post_availability(user_id)