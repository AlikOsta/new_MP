"""
Routers package for API endpoints
"""
from .categories import router as categories_router
from .posts import router as posts_router  
from .packages import router as packages_router
from .admin import router as admin_router
from .users import router as users_router
from .webhook import router as webhook_router