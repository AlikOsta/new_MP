from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from core.database import get_database
from models.post import PostJob, PostServices, PostJobCreate, PostServicesCreate, PostUpdate, PostStatus, Favorite

router = APIRouter(prefix="/api/posts", tags=["posts"])

@router.get("/", response_model=List[dict])
async def get_posts(
    post_type: Optional[str] = Query(None, description="job or service"),
    super_rubric_id: Optional[str] = None,
    sub_rubric_id: Optional[str] = None,
    city_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db=Depends(get_database)
):
    query = {"status": PostStatus.ACTIVE}
    
    if post_type:
        query["post_type"] = post_type
    if super_rubric_id:
        query["super_rubric_id"] = super_rubric_id
    if sub_rubric_id:
        query["sub_rubric_id"] = sub_rubric_id
    if city_id:
        query["city_id"] = city_id
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.posts.find(query).skip(skip).limit(limit).sort("created_at", -1)
    posts = []
    async for doc in cursor:
        if doc["post_type"] == "job":
            posts.append(PostJob(**doc).model_dump())
        else:
            posts.append(PostServices(**doc).model_dump())
    
    return posts

@router.get("/{post_id}", response_model=dict)
async def get_post(post_id: str, db=Depends(get_database)):
    post = await db.posts.find_one({"_id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment views
    await db.posts.update_one(
        {"_id": post_id},
        {"$inc": {"views_count": 1}}
    )
    
    if post["post_type"] == "job":
        return PostJob(**post).model_dump()
    else:
        return PostServices(**post).model_dump()

@router.post("/jobs", response_model=PostJob)
async def create_job_post(post: PostJobCreate, author_id: str, db=Depends(get_database)):
    post_dict = post.model_dump()
    post_dict["author_id"] = author_id
    post_dict["post_type"] = "job"
    
    result = await db.posts.insert_one(post_dict)
    created_post = await db.posts.find_one({"_id": result.inserted_id})
    return PostJob(**created_post)

@router.post("/services", response_model=PostServices)
async def create_service_post(post: PostServicesCreate, author_id: str, db=Depends(get_database)):
    post_dict = post.model_dump()
    post_dict["author_id"] = author_id
    post_dict["post_type"] = "service"
    
    result = await db.posts.insert_one(post_dict)
    created_post = await db.posts.find_one({"_id": result.inserted_id})
    return PostServices(**created_post)

@router.put("/{post_id}", response_model=dict)
async def update_post(post_id: str, post_update: PostUpdate, db=Depends(get_database)):
    update_data = {k: v for k, v in post_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.posts.update_one(
        {"_id": post_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    updated_post = await db.posts.find_one({"_id": post_id})
    if updated_post["post_type"] == "job":
        return PostJob(**updated_post).model_dump()
    else:
        return PostServices(**updated_post).model_dump()

@router.delete("/{post_id}")
async def delete_post(post_id: str, db=Depends(get_database)):
    result = await db.posts.delete_one({"_id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

# Favorites
@router.post("/favorites")
async def add_to_favorites(user_id: str, post_id: str, db=Depends(get_database)):
    # Check if already in favorites
    existing = await db.favorites.find_one({"user_id": user_id, "post_id": post_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")
    
    favorite_dict = {"user_id": user_id, "post_id": post_id}
    await db.favorites.insert_one(favorite_dict)
    return {"message": "Added to favorites"}

@router.delete("/favorites")
async def remove_from_favorites(user_id: str, post_id: str, db=Depends(get_database)):
    result = await db.favorites.delete_one({"user_id": user_id, "post_id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not in favorites")
    return {"message": "Removed from favorites"}

@router.get("/favorites/{user_id}", response_model=List[dict])
async def get_user_favorites(user_id: str, db=Depends(get_database)):
    # Get favorite post IDs
    cursor = db.favorites.find({"user_id": user_id})
    post_ids = [fav["post_id"] async for fav in cursor]
    
    if not post_ids:
        return []
    
    # Get posts
    cursor = db.posts.find({"_id": {"$in": post_ids}})
    posts = []
    async for doc in cursor:
        if doc["post_type"] == "job":
            posts.append(PostJob(**doc).model_dump())
        else:
            posts.append(PostServices(**doc).model_dump())
    
    return posts