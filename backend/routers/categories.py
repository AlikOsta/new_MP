"""
Categories and reference data router
"""
from fastapi import APIRouter
from database import db

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("/super-rubrics")
async def get_super_rubrics():
    """Get all active super rubrics (categories)"""
    results = await db.fetchall("SELECT id, name_ru, name_ua, icon FROM super_rubrics WHERE is_active = 1")
    return results

@router.get("/cities")
async def get_cities():
    """Get all active cities"""
    results = await db.fetchall("SELECT id, name_ru, name_ua FROM cities WHERE is_active = 1")
    return results

@router.get("/currencies")
async def get_currencies():
    """Get all active currencies"""
    results = await db.fetchall("SELECT id, code, name_ru, name_ua, symbol FROM currencies WHERE is_active = 1")
    return results

@router.get("/all")
async def get_all_reference_data():
    """
    Get all reference data in one request for Telegram Mini App optimization
    This reduces the number of API calls from 4+ to 1
    """
    # Fetch all reference data in parallel
    super_rubrics = await db.fetchall("SELECT id, name_ru, name_ua, icon FROM super_rubrics WHERE is_active = 1")
    cities = await db.fetchall("SELECT id, name_ru, name_ua FROM cities WHERE is_active = 1")
    currencies = await db.fetchall("SELECT id, code, name_ru, name_ua, symbol FROM currencies WHERE is_active = 1")
    packages = await db.fetchall("""
        SELECT id, name_ru, name_ua, package_type, price, currency_id, 
               duration_days, post_lifetime_days, features_ru, features_ua,
               has_photo, has_highlight, has_boost, sort_order
        FROM packages WHERE is_active = 1 ORDER BY sort_order ASC
    """)
    
    # Parse features from pipe-separated strings
    for package in packages:
        if package.get("features_ru"):
            package["features_ru"] = package["features_ru"].split("|")
        if package.get("features_ua"):
            package["features_ua"] = package["features_ua"].split("|")
    
    return {
        "categories": super_rubrics,
        "cities": cities,
        "currencies": currencies,
        "packages": packages
    }