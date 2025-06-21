"""
Validation utilities
"""
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15

def validate_price(price: Optional[float]) -> bool:
    """Validate price value"""
    if price is None:
        return True
    
    return isinstance(price, (int, float)) and price >= 0

def validate_post_type(post_type: str) -> bool:
    """Validate post type"""
    valid_types = ["job", "service"]
    return post_type in valid_types

def validate_status(status: int) -> bool:
    """Validate post status"""
    valid_statuses = [1, 2, 3, 4, 5]  # Draft, Moderation, Manual Review, Published, Blocked
    return status in valid_statuses

def sanitize_text(text: str) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def validate_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram user ID"""
    return isinstance(telegram_id, int) and telegram_id > 0