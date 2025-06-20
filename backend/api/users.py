from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from core.database import get_database
from models.user import TelegramUser, UserCreate, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=TelegramUser)
async def create_user(user: UserCreate, db=Depends(get_database)):
    # Check if user already exists
    existing_user = await db.users.find_one({"telegram_id": user.telegram_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_dict = user.model_dump()
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return TelegramUser(**created_user)

@router.get("/{user_id}", response_model=TelegramUser)
async def get_user(user_id: str, db=Depends(get_database)):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TelegramUser(**user)

@router.get("/telegram/{telegram_id}", response_model=TelegramUser)
async def get_user_by_telegram_id(telegram_id: int, db=Depends(get_database)):
    user = await db.users.find_one({"telegram_id": telegram_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TelegramUser(**user)

@router.put("/{user_id}", response_model=TelegramUser)
async def update_user(user_id: str, user_update: UserUpdate, db=Depends(get_database)):
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"_id": user_id})
    return TelegramUser(**updated_user)