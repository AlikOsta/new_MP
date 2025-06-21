"""
Main FastAPI application - clean and modular architecture
Replaces the monolithic server.py with proper separation of concerns
"""
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config import CORS_ORIGINS

# Import AI Moderation and Background Tasks
# Temporarily disabled AI moderation due to httpcore issues
# from ai_moderation import init_moderation_services
# from background_tasks import start_background_tasks, stop_background_tasks

# Import all routers
from routers import (
    admin_router,
    categories_router,
    packages_router,
    posts_router,
    users_router,
    webhook_router
)

# Lifespan manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    print("🚀 Starting Telegram Marketplace API...")
    
    # Initialize AI moderation services - temporarily disabled
    # await init_moderation_services()
    # print("✅ AI moderation services initialized")
    
    # Start background tasks - temporarily disabled
    # await start_background_tasks()
    # print("✅ Background tasks started")
    
    print("🎉 Application startup complete!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    # await stop_background_tasks()
    print("✅ Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Telegram Marketplace API",
    description="Modular API for Telegram Mini App Marketplace",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(admin_router)
app.include_router(categories_router)
app.include_router(packages_router)
app.include_router(posts_router)
app.include_router(users_router)
app.include_router(webhook_router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy", 
        "message": "Telegram Marketplace API is running",
        "version": "2.0.0",
        "architecture": "modular"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Telegram Marketplace API", 
        "docs": "/docs",
        "version": "2.0.0",
        "architecture": "Clean modular architecture - no more monolithic server.py!"
    }

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    print(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)