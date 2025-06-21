"""
Configuration module for the Telegram Marketplace API
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/telegram_marketplace')

# Admin credentials (from environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# AI Moderation configuration
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000"
]

# API settings
API_PREFIX = "/api"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50

# Post settings
DEFAULT_POST_LIFETIME_DAYS = 30
FREE_POST_COOLDOWN_DAYS = 7