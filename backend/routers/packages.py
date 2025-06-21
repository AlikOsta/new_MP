"""
Packages router - handles package operations
"""
from fastapi import APIRouter
from database import db

router = APIRouter(prefix="/api/packages", tags=["packages"])

@router.get("/")
async def get_packages():
    """Get all active packages"""
    results = await db.fetchall("SELECT * FROM packages WHERE is_active = 1 ORDER BY sort_order ASC")
    
    # Parse features from pipe-separated strings
    for package in results:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return results

@router.get("/{package_id}")
async def get_package(package_id: str):
    """Get a specific package by ID"""
    package = await db.fetchone("SELECT * FROM packages WHERE id = ? AND is_active = 1", [package_id])
    
    if not package:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Parse features
    if package.get("features_ru"):
        package["features_ru"] = package["features_ru"].split("|")
    if package.get("features_ua"):
        package["features_ua"] = package["features_ua"].split("|")
    
    return package