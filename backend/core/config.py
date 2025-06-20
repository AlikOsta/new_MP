import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "telegram_marketplace")
    
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_payments_token: str = os.getenv("TELEGRAM_PAYMENTS_TOKEN", "")
    webhook_url: Optional[str] = os.getenv("WEBHOOK_URL")
    
    # Mistral AI
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()