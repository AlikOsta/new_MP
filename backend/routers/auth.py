"""
Authentication router - handles secure Telegram authentication
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from database import db
from datetime import datetime, timedelta
from utils.telegram_auth import (
    validate_telegram_init_data, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class TelegramAuthRequest(BaseModel):
    init_data: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    expires_in: int

@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram_user(auth_request: TelegramAuthRequest):
    """
    Authenticate user with Telegram WebApp initData
    Returns JWT token if authentication is successful
    """
    try:
        # Validate Telegram initData
        validated_data = validate_telegram_init_data(auth_request.init_data)
        user_data = validated_data['user']
        
        if not user_data or 'id' not in user_data:
            raise HTTPException(status_code=400, detail="Invalid user data from Telegram")
        
        telegram_id = user_data['id']
        
        # Check if user exists in database
        existing_user = await db.fetchone(
            "SELECT * FROM users WHERE telegram_id = ?", 
            [telegram_id]
        )
        
        # Prepare user data for database
        db_user_data = {
            "telegram_id": telegram_id,
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username", ""),
            "language": user_data.get("language_code", "ru"),
            "updated_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        if existing_user:
            # Update existing user
            await db.update("users", db_user_data, "telegram_id = ?", [telegram_id])
            user_id = existing_user["id"]
            db_user_data["id"] = user_id
            db_user_data["created_at"] = existing_user["created_at"]
        else:
            # Create new user
            db_user_data["created_at"] = datetime.now().isoformat()
            user_id = await db.insert("users", db_user_data)
            db_user_data["id"] = user_id
        
        # Create JWT token
        token_data = {
            "sub": str(user_id),
            "telegram_id": telegram_id,
            "username": user_data.get("username", ""),
            "first_name": user_data.get("first_name", ""),
            "auth_date": validated_data['auth_date']
        }
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=db_user_data,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/verify")
async def verify_authentication(request: Request):
    """
    Verify current authentication status
    """
    from utils.telegram_auth import get_current_user_from_token
    
    try:
        user_payload = get_current_user_from_token(request)
        
        # Get full user data from database
        user = await db.fetchone(
            "SELECT * FROM users WHERE id = ?", 
            [user_payload['sub']]
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "authenticated": True,
            "user": dict(user),
            "token_payload": user_payload
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout():
    """
    Logout user (client should discard the token)
    """
    return {"message": "Logout successful. Please discard your access token."}

@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current user information
    """
    from utils.telegram_auth import get_current_user_from_token
    
    user_payload = get_current_user_from_token(request)
    
    # Get full user data from database
    user = await db.fetchone(
        "SELECT * FROM users WHERE id = ?", 
        [user_payload['sub']]
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return dict(user)