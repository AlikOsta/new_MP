"""
Authentication utilities for Telegram WebApp
"""
import hmac
import hashlib
import json
from urllib.parse import unquote, parse_qsl
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from config import SECRET_KEY
import os

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

def validate_telegram_init_data(init_data: str) -> dict:
    """
    Validate Telegram WebApp initData
    Returns user data if valid, raises ValueError if invalid
    """
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("Telegram bot token not configured")
    
    try:
        # Parse the init_data
        parsed_data = dict(parse_qsl(unquote(init_data)))
        
        # Extract hash
        received_hash = parsed_data.pop('hash', '')
        if not received_hash:
            raise ValueError("Hash missing from init data")
        
        # Create data check string
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
        
        # Create secret key
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Verify hash
        if not hmac.compare_digest(calculated_hash, received_hash):
            raise ValueError("Invalid hash - data may be tampered")
        
        # Check auth_date (data should not be older than 1 day)
        auth_date = int(parsed_data.get('auth_date', 0))
        current_time = datetime.now().timestamp()
        if current_time - auth_date > 24 * 60 * 60:  # 24 hours
            raise ValueError("Init data is too old")
        
        # Parse user data
        user_data = json.loads(parsed_data.get('user', '{}'))
        
        return {
            'user': user_data,
            'auth_date': auth_date,
            'query_id': parsed_data.get('query_id'),
            'start_param': parsed_data.get('start_param')
        }
        
    except Exception as e:
        raise ValueError(f"Failed to validate Telegram data: {str(e)}")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")

def get_current_user_from_token(request: Request) -> dict:
    """Get current user from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        return payload
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_telegram_user_id(request: Request) -> str:
    """Extract and validate Telegram user ID from X-Telegram-User-ID header"""
    telegram_user_id = request.headers.get("X-Telegram-User-ID")
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="Telegram user ID required")
    
    try:
        # Verify it's a valid integer
        int(telegram_user_id)
        return telegram_user_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Telegram user ID")