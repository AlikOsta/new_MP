"""
Posts router - handles job and service posts
This router uses PostService to eliminate code duplication
"""
from fastapi import APIRouter, Request, HTTPException
from services.post_service import PostService
from services.moderation_service import ModerationService
from database import db
from datetime import datetime

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("/")
async def get_posts(
    post_type: str = None, 
    search: str = None, 
    author_id: str = None,
    super_rubric_id: str = None,
    city_id: str = None,
    page: int = 1,
    limit: int = 20
):
    """Get posts with filters and pagination"""
    filters = {
        "post_type": post_type,
        "search": search,
        "author_id": author_id,
        "super_rubric_id": super_rubric_id,
        "city_id": city_id,
        "page": page,
        "limit": limit
    }
    
    return await PostService.get_posts_with_filters(filters)

@router.post("/jobs")
async def create_job_post(request: Request):
    """Create a job post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID")
    
    if not author_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use unified service method (eliminates code duplication!)
        post_data = await PostService.create_post(
            post_data=data,
            post_type="job",
            author_id=author_id,
            package_id=data.get("package_id")
        )
        
        # Handle AI moderation
        moderation_result = await ModerationService.moderate_post(post_data)
        post_data.update(moderation_result)
        
        return post_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job post: {str(e)}")

@router.post("/services")
async def create_service_post(request: Request):
    """Create a service post"""
    data = await request.json()
    author_id = request.headers.get("X-Author-ID")
    
    if not author_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use unified service method (eliminates code duplication!)
        post_data = await PostService.create_post(
            post_data=data,
            post_type="service",
            author_id=author_id,
            package_id=data.get("package_id")
        )
        
        # Handle AI moderation
        moderation_result = await ModerationService.moderate_post(post_data)
        post_data.update(moderation_result)
        
        return post_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating service post: {str(e)}")

@router.put("/{post_id}/status")
async def update_post_status(post_id: str, request: Request):
    """Update post status"""
    data = await request.json()
    status = data.get("status", 3)
    
    success = await PostService.update_post_status(post_id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"message": "Status updated successfully"}

@router.get("/{post_id}")
async def get_post(post_id: str):
    """Get a single post by ID"""
    post = await db.fetchone("SELECT * FROM posts WHERE id = ?", [post_id])
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    await db.update("posts", {"views_count": post["views_count"] + 1}, "id = ?", [post_id])
    post["views_count"] += 1
    
    return post

# Favorites endpoints
@router.post("/favorites")
async def add_to_favorites(request: Request):
    """Add post to favorites"""
    data = await request.json()
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    
    if not user_id or not post_id:
        raise HTTPException(status_code=400, detail="user_id and post_id are required")
    
    # Check if already in favorites
    existing = await db.fetchone("SELECT id FROM favorites WHERE user_id = ? AND post_id = ?", [user_id, post_id])
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")
    
    favorite_data = {
        "user_id": user_id, 
        "post_id": post_id,
        "created_at": datetime.now().isoformat()
    }
    
    await db.insert("favorites", favorite_data)
    return {"message": "Added to favorites"}

@router.delete("/favorites")
async def remove_from_favorites(request: Request):
    """Remove post from favorites"""
    data = await request.json()
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    
    if not user_id or not post_id:
        raise HTTPException(status_code=400, detail="user_id and post_id are required")
    
    rows_affected = await db.delete("favorites", "user_id = ? AND post_id = ?", [user_id, post_id])
    
    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Removed from favorites"}

@router.get("/favorites/{user_id}")
async def get_user_favorites(user_id: str):
    """Get user's favorite posts"""
    favorites = await db.fetchall("""
        SELECT p.* FROM posts p
        INNER JOIN favorites f ON p.id = f.post_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """, [user_id])
    
    return favorites