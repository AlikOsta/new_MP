"""
Routers package for API endpoints
"""
from .admin import router as admin_router
from .categories import router as categories_router
from .packages import router as packages_router
from .posts import router as posts_router
from .users import router as users_router
from .webhook import router as webhook_router

__all__ = [
    "admin_router",
    "categories_router", 
    "packages_router",
    "posts_router",
    "users_router",
    "webhook_router"
]