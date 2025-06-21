"""
Post service - business logic for posts
This service eliminates code duplication between job and service posts
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database import db
from config import DEFAULT_POST_LIFETIME_DAYS, FREE_POST_COOLDOWN_DAYS

class PostService:
    """Service for handling post operations"""
    
    @staticmethod
    async def create_post(post_data: Dict[str, Any], post_type: str, author_id: str, package_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Unified method for creating posts (eliminates duplication between jobs and services)
        """
        # Check if user can create free post
        if not package_id or package_id == "free-package":
            can_create_result = await PostService.check_free_post_availability(author_id)
            if not can_create_result["can_create_free"]:
                raise ValueError(f"Free post not available yet. Next free at: {can_create_result['next_free_at']}")
        
        # Get package details
        package = await db.fetchone("SELECT * FROM packages WHERE id = ?", [package_id]) if package_id else None
        
        # Calculate expiration date
        lifetime_days = package["post_lifetime_days"] if package else DEFAULT_POST_LIFETIME_DAYS
        expires_at = (datetime.now() + timedelta(days=lifetime_days)).isoformat()
        
        # Prepare post data
        post_record = {
            "id": str(uuid.uuid4()),
            "title": post_data.get("title"),
            "description": post_data.get("description"),
            "post_type": post_type,
            "price": post_data.get("price"),
            "currency_id": post_data.get("currency_id"),
            "city_id": post_data.get("city_id"),
            "super_rubric_id": post_data.get("super_rubric_id"),
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
        
        # Insert post
        post_id = await db.insert("posts", post_record)
        post_record["id"] = post_id
        
        # Handle free post tracking
        if not package_id or package_id == "free-package":
            await PostService._record_free_post_usage(author_id)
        
        # Schedule boosts if needed
        if package and package["has_boost"]:
            await PostService._schedule_post_boost(post_id, package)
        
        return post_record
    
    @staticmethod
    async def check_free_post_availability(user_id: str) -> Dict[str, Any]:
        """Check if user can create a free post"""
        # Get user's last free post
        last_free = await db.fetchone(
            "SELECT * FROM user_free_posts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            [user_id]
        )
        
        if not last_free:
            return {"can_create_free": True, "next_free_at": None}
        
        # Check if cooldown period has passed
        next_free_time = datetime.fromisoformat(last_free["next_free_post_at"])
        can_create = datetime.now() >= next_free_time
        
        return {
            "can_create_free": can_create,
            "next_free_at": last_free["next_free_post_at"] if not can_create else None
        }
    
    @staticmethod
    async def _record_free_post_usage(user_id: str):
        """Record free post usage"""
        next_free_date = (datetime.now() + timedelta(days=FREE_POST_COOLDOWN_DAYS)).isoformat()
        free_post_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "next_free_post_at": next_free_date
        }
        await db.insert("user_free_posts", free_post_data)
    
    @staticmethod
    async def _schedule_post_boost(post_id: str, package: Dict[str, Any]):
        """Schedule post boost"""
        boost_data = {
            "post_id": post_id,
            "next_boost_at": (datetime.now() + timedelta(days=package["boost_interval_days"])).isoformat(),
            "boost_count": 0,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        await db.insert("post_boost_schedule", boost_data)
    
    @staticmethod
    async def get_posts_with_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get posts with filters and pagination"""
        # Extract parameters
        post_type = filters.get("post_type")
        search = filters.get("search")
        author_id = filters.get("author_id")
        super_rubric_id = filters.get("super_rubric_id")
        city_id = filters.get("city_id")
        page = max(1, filters.get("page", 1))
        limit = min(50, max(1, filters.get("limit", 20)))
        
        offset = (page - 1) * limit
        
        # Build query
        query = """SELECT id, title, description, post_type, price, currency_id, city_id, 
                          super_rubric_id, author_id, status, has_photo, has_highlight, 
                          has_boost, views_count, created_at, expires_at 
                   FROM posts WHERE 1=1"""
        params = []
        
        if post_type:
            query += " AND post_type = ?"
            params.append(post_type)
        
        if search:
            query += " AND (title LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        if author_id:
            query += " AND author_id = ?"
            params.append(author_id)
        
        if super_rubric_id:
            query += " AND super_rubric_id = ?"
            params.append(super_rubric_id)
        
        if city_id:
            query += " AND city_id = ?"
            params.append(city_id)
        
        # Add ordering and pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        posts = await db.fetchall(query, params)
        
        # Count total posts
        count_query = "SELECT COUNT(*) as total FROM posts WHERE 1=1"
        count_params = []
        
        if post_type:
            count_query += " AND post_type = ?"
            count_params.append(post_type)
        
        if search:
            count_query += " AND (title LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            count_params.extend([search_term, search_term])
        
        if author_id:
            count_query += " AND author_id = ?"
            count_params.append(author_id)
        
        if super_rubric_id:
            count_query += " AND super_rubric_id = ?"
            count_params.append(super_rubric_id)
        
        if city_id:
            count_query += " AND city_id = ?"
            count_params.append(city_id)
        
        total_result = await db.fetchone(count_query, count_params)
        total = total_result["total"] if total_result else 0
        
        return {
            "posts": posts,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    async def update_post_status(post_id: str, status: int) -> bool:
        """Update post status"""
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        rows_affected = await db.update("posts", update_data, "id = ?", [post_id])
        return rows_affected > 0